from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
import models
import json
import time
import threading
import os
from typing import Any, cast
from concurrent.futures import ThreadPoolExecutor, as_completed

import dashscope

app = FastAPI(title="Nuna Prelabel Service")

MAX_CONCURRENT_JOBS = max(1, int(os.getenv("PRELABEL_MAX_CONCURRENT_JOBS", "2")))
ASR_MAX_WORKERS = max(1, int(os.getenv("PRELABEL_ASR_MAX_WORKERS", "3")))
_JOB_SEMAPHORE = threading.Semaphore(MAX_CONCURRENT_JOBS)
_ACTIVE_DAY_KEYS: set[tuple[str, str]] = set()
_ACTIVE_DAY_KEYS_LOCK = threading.Lock()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_asr_provider() -> str:
    return os.getenv("PRELABEL_ASR_PROVIDER", "mock").strip().lower()


def _get_audio_root() -> str:
    return os.getenv("RUNTIME_AUDIO_DIR", "/runtime/data/audio").strip()


def _resolve_audio_file_path(stored_path: str) -> str:
    if not stored_path:
        return ""
    if os.path.isabs(stored_path):
        return stored_path
    return os.path.join(_get_audio_root(), stored_path)


def _response_to_dict(response: Any) -> dict:
    if isinstance(response, dict):
        return response
    if hasattr(response, "to_dict"):
        converted = response.to_dict()
        if isinstance(converted, dict):
            return converted
    if hasattr(response, "dict"):
        converted = response.dict()
        if isinstance(converted, dict):
            return converted
    if hasattr(response, "__dict__"):
        return dict(response.__dict__)
    return {"raw": str(response)}


def _serialize_asr_result(
    provider: str,
    provider_schema_version: str,
    text: str | None,
    language: str | None,
    emotion: str | None,
    finish_reason: str | None,
    usage: dict | None,
    status_code: int | None,
    request_id: str | None,
    message: str | None,
    code: str | None,
    provider_output: dict | None = None,
    raw_response: dict | None = None,
) -> dict:
    data = {
        "provider": provider,
        "provider_schema_version": provider_schema_version,
        "normalized": {
            "text": text,
            "language": language,
            "emotion": emotion,
            "finish_reason": finish_reason,
        },
        "provider_output": provider_output or {},
        "usage": usage or {},
        "status_code": status_code,
        "request_id": request_id,
        "message": message,
        "code": code,
    }
    if raw_response is not None and _env_bool("PRELABEL_ASR_STORE_RAW_RESPONSE", False):
        data["raw_response"] = raw_response
    return data


def _normalize_dashscope_asr(provider_name: str, payload: dict) -> dict:
    output = payload.get("output") or {}
    choices = output.get("choices") or []
    first_choice = choices[0] if choices else {}
    message = first_choice.get("message") or {}
    content_items = message.get("content") or []
    annotations = message.get("annotations") or []

    text = None
    if isinstance(content_items, list):
        for item in content_items:
            if isinstance(item, dict) and item.get("text"):
                text = item.get("text")
                break

    language = None
    emotion = None
    if isinstance(annotations, list):
        for item in annotations:
            if not isinstance(item, dict):
                continue
            if language is None and item.get("language"):
                language = item.get("language")
            if emotion is None and item.get("emotion"):
                emotion = item.get("emotion")

    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}

    return _serialize_asr_result(
        provider=provider_name,
        provider_schema_version="dashscope.multimodalconversation.v1",
        text=text,
        language=language,
        emotion=emotion,
        finish_reason=first_choice.get("finish_reason") or output.get("finish_reason"),
        usage=usage,
        status_code=payload.get("status_code"),
        request_id=payload.get("request_id"),
        message=payload.get("message"),
        code=payload.get("code"),
        provider_output={
            "choices": choices,
            "audio": output.get("audio"),
        },
        raw_response=payload,
    )


def _call_dashscope_qwen3_asr_flash(audio_abs_path: str) -> dict:
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1").strip()
    dashscope.base_http_api_url = base_url

    # Prefer env-file key, then fallback to host-injected key when provided.
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("HOST_DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY")

    model = os.getenv("DASHSCOPE_ASR_MODEL", "qwen3-asr-flash").strip()
    language = os.getenv("PRELABEL_ASR_LANGUAGE", "").strip()
    enable_itn = _env_bool("PRELABEL_ASR_ENABLE_ITN", False)

    asr_options: dict[str, Any] = {"enable_itn": enable_itn}
    if language:
        asr_options["language"] = language

    messages = [
        {"role": "user", "content": [{"audio": f"file://{audio_abs_path}"}]},
    ]

    response = dashscope.MultiModalConversation.call(
        api_key=api_key,
        model=model,
        messages=messages,
        result_format="message",
        asr_options=asr_options,
    )
    payload = _response_to_dict(response)
    return _normalize_dashscope_asr("dashscope_qwen3_asr_flash", payload)


def _run_asr(audio_abs_path: str) -> dict:
    provider = _get_asr_provider()
    if provider == "mock":
        filename = os.path.basename(audio_abs_path)
        return _serialize_asr_result(
            provider="mock",
            provider_schema_version="mock.v1",
            text=f"[mock-asr] {filename}",
            language=None,
            emotion=None,
            finish_reason="mock_stop",
            usage={},
            status_code=200,
            request_id=None,
            message="mock response",
            code="",
            provider_output={},
        )
    if provider == "dashscope_qwen3_asr_flash":
        return _call_dashscope_qwen3_asr_flash(audio_abs_path)
    raise RuntimeError(f"不支持的 PRELABEL_ASR_PROVIDER: {provider}")


class RunRequest(BaseModel):
    job_id: int
    day_id: str
    user_id: str


def _set_job_running(job: Any, pipeline_suffix: str = ""):
    now = int(time.time())
    job.status = "running"
    job.started_at = now
    job.finished_at = None
    job.error_log = None
    base_version = os.getenv("PRELABEL_PIPELINE_VERSION", "mvp-asr-v1")
    job.pipeline_version = f"{base_version}{pipeline_suffix}"


def _set_job_finished(job: Any, failed_count: int, sample_errors: list[str] | None = None):
    job.finished_at = int(time.time())
    if failed_count > 0:
        job.status = "failed"
        details = "; ".join((sample_errors or [])[:3])
        job.error_log = f"ASR失败片段数={failed_count}" + (f"; 示例: {details}" if details else "")
        return
    job.status = "done"
    job.error_log = None


def _insert_asr_result(db: Session, job_id: int, user_id: str, day_id: str, row: Any, asr_payload: dict):
    db.add(models.PrelabelResult(
        job_id=job_id,
        userId=user_id,
        day_id=day_id,
        audio_id=row.id,
        minute_ts=row.start_ts,
        task_type="asr",
        content_json=json.dumps(asr_payload, ensure_ascii=False),
        created_at=int(time.time()),
    ))


def _insert_mock_sed_result(db: Session, job_id: int, user_id: str, day_id: str, row: Any):
    if not _env_bool("PRELABEL_ENABLE_MOCK_SED_RESULT", False):
        return
    sed_payload = {
        "provider": "mock",
        "provider_schema_version": "mock.v1",
        "block_label": "安静的室内",
        "point_label": "轻微环境声波动",
        "emotion": "mid/low",
    }
    db.add(models.PrelabelResult(
        job_id=job_id,
        userId=user_id,
        day_id=day_id,
        audio_id=row.id,
        minute_ts=row.start_ts,
        task_type="sed_asc_har",
        content_json=json.dumps(sed_payload, ensure_ascii=False),
        created_at=int(time.time()),
    ))


def _acquire_day_key(user_id: str, day_id: str) -> bool:
    key = (user_id, day_id)
    with _ACTIVE_DAY_KEYS_LOCK:
        if key in _ACTIVE_DAY_KEYS:
            return False
        _ACTIVE_DAY_KEYS.add(key)
        return True


def _release_day_key(user_id: str, day_id: str):
    key = (user_id, day_id)
    with _ACTIVE_DAY_KEYS_LOCK:
        _ACTIVE_DAY_KEYS.discard(key)


def _run_single_asr(row_id: int, file_path: str, start_ts: int) -> dict:
    audio_abs_path = _resolve_audio_file_path(str(file_path))
    if not os.path.exists(audio_abs_path):
        raise RuntimeError(f"音频文件不存在: path={audio_abs_path}")
    asr_payload = _run_asr(audio_abs_path)
    return {
        "row_id": row_id,
        "start_ts": start_ts,
        "asr_payload": asr_payload,
    }


def _run_pipeline(job_id: int, day_id: str, user_id: str, failed_only: bool = False):
    _JOB_SEMAPHORE.acquire()
    db: Session = SessionLocal()
    try:
        job = db.query(models.PrelabelJob).filter(
            models.PrelabelJob.id == job_id,
            models.PrelabelJob.userId == user_id,
            models.PrelabelJob.day_id == day_id,
        ).first()
        if not job:
            return
        job = cast(Any, job)

        _set_job_running(job, pipeline_suffix="-rerun-failed" if failed_only else "")
        db.commit()

        rows_query = db.query(models.AudioData).filter(
            models.AudioData.userId == user_id,
            models.AudioData.date == day_id,
        )
        if failed_only:
            rows_query = rows_query.filter(models.AudioData.pre_label_status == "failed")
        rows = rows_query.order_by(models.AudioData.start_ts.asc()).all()

        db.query(models.PrelabelResult).filter(
            models.PrelabelResult.job_id == job.id,
            models.PrelabelResult.userId == user_id,
            models.PrelabelResult.day_id == day_id,
        ).delete()
        db.commit()

        if not rows:
            _set_job_finished(job, failed_count=0)
            db.commit()
            return

        failed_count = 0
        sample_errors: list[str] = []

        row_map: dict[int, Any] = {}
        tasks: list[tuple[int, str, int]] = []
        for row in rows:
            row = cast(Any, row)
            row.pre_label_status = "running"
            row_map[int(row.id)] = row
            tasks.append((int(row.id), str(row.file_path), int(row.start_ts)))
        db.commit()

        with ThreadPoolExecutor(max_workers=min(ASR_MAX_WORKERS, len(tasks))) as executor:
            future_map = {
                executor.submit(_run_single_asr, row_id, file_path, start_ts): row_id
                for row_id, file_path, start_ts in tasks
            }
            for future in as_completed(future_map):
                row_id = future_map[future]
                row = row_map.get(row_id)
                if row is None:
                    continue
                try:
                    result = future.result()
                    asr_payload = cast(dict, result["asr_payload"])
                    _insert_asr_result(db, int(job.id), user_id, day_id, row, asr_payload)
                    _insert_mock_sed_result(db, int(job.id), user_id, day_id, row)
                    row.pre_label_status = "done"
                    db.commit()
                except Exception as row_exc:
                    db.rollback()
                    row_ref = db.query(models.AudioData).filter(models.AudioData.id == row_id).first()
                    if row_ref:
                        row_ref = cast(Any, row_ref)
                        row_ref.pre_label_status = "failed"
                    failed_count += 1
                    if len(sample_errors) < 5:
                        sample_errors.append(f"audio_id={row_id}: {str(row_exc)[:120]}")
                    db.commit()

        _set_job_finished(job, failed_count=failed_count, sample_errors=sample_errors)
        db.commit()
    except Exception as exc:
        db.rollback()
        failed_rows = db.query(models.AudioData).filter(
            models.AudioData.userId == user_id,
            models.AudioData.date == day_id,
            models.AudioData.pre_label_status == "running",
        ).all()
        for r in failed_rows:
            r = cast(Any, r)
            r.pre_label_status = "failed"
        failed_job = db.query(models.PrelabelJob).filter(models.PrelabelJob.id == job_id).first()
        if failed_job:
            failed_job = cast(Any, failed_job)
            failed_job.status = "failed"
            failed_job.finished_at = int(time.time())
            failed_job.error_log = str(exc)[:500]
            db.commit()
    finally:
        db.close()
        _JOB_SEMAPHORE.release()
        _release_day_key(user_id, day_id)


@app.post("/prelabel/run")
def run_prelabel(req: RunRequest):
    db: Session = SessionLocal()
    try:
        job = db.query(models.PrelabelJob).filter(
            models.PrelabelJob.id == req.job_id,
            models.PrelabelJob.userId == req.user_id,
            models.PrelabelJob.day_id == req.day_id,
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="job 不存在")

        if job.status in ("running", "done"):
            return {"accepted": True, "job_id": job.id, "status": job.status, "reused": True}

        if not _acquire_day_key(req.user_id, req.day_id):
            return {
                "accepted": True,
                "job_id": job.id,
                "status": "running",
                "reused": True,
                "message": "同一用户同一天的预标注正在执行",
            }

        t = threading.Thread(
            target=_run_pipeline,
            args=(req.job_id, req.day_id, req.user_id, False),
            daemon=True,
        )
        t.start()
        return {"accepted": True, "job_id": job.id, "status": "pending", "reused": False}
    finally:
        db.close()


@app.post("/prelabel/rerun_failed")
def rerun_failed_prelabel(req: RunRequest):
    db: Session = SessionLocal()
    try:
        job = db.query(models.PrelabelJob).filter(
            models.PrelabelJob.id == req.job_id,
            models.PrelabelJob.userId == req.user_id,
            models.PrelabelJob.day_id == req.day_id,
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="job 不存在")

        if job.status in ("running", "done"):
            return {"accepted": True, "job_id": job.id, "status": job.status, "reused": True}

        failed_exists = db.query(models.AudioData.id).filter(
            models.AudioData.userId == req.user_id,
            models.AudioData.date == req.day_id,
            models.AudioData.pre_label_status == "failed",
        ).first()
        if not failed_exists:
            return {
                "accepted": True,
                "job_id": job.id,
                "status": "done",
                "reused": True,
                "message": "没有失败片段需要重跑",
            }

        if not _acquire_day_key(req.user_id, req.day_id):
            return {
                "accepted": True,
                "job_id": job.id,
                "status": "running",
                "reused": True,
                "message": "同一用户同一天的预标注正在执行",
            }

        t = threading.Thread(
            target=_run_pipeline,
            args=(req.job_id, req.day_id, req.user_id, True),
            daemon=True,
        )
        t.start()
        return {"accepted": True, "job_id": job.id, "status": "pending", "reused": False}
    finally:
        db.close()


@app.get("/prelabel/status/{job_id}")
def prelabel_status(job_id: int):
    db: Session = SessionLocal()
    try:
        job = db.query(models.PrelabelJob).filter(models.PrelabelJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="job 不存在")
        return {
            "id": job.id,
            "day_id": job.day_id,
            "status": job.status,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "error_log": job.error_log,
            "pipeline_version": job.pipeline_version,
        }
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}

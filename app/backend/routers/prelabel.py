from fastapi import APIRouter, Request, Depends, HTTPException, Body, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from ..database import get_db
from ..dependencies import templates
from .. import models
from ..i18n import t
from .tasks import require_login
import os
import time
import json
import httpx
import re
import io
import csv
import zipfile
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["prelabel"])

ACTIVE_JOB_STALE_SECONDS = int(os.getenv("PRELABEL_ACTIVE_JOB_STALE_SECONDS", "3600"))
ALLOW_REPEAT_PRELABEL = (os.getenv("PRELABEL_ALLOW_REPEAT", "true") or "true").strip().lower() in {"1", "true", "yes", "on"}
ASR_VAD_THRES = max(1, int(os.getenv("ASR_VAD_THRES", "15")))


def _serialize_job(job: models.PrelabelJob):
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


def _parse_content(content_json: str):
    try:
        return json.loads(content_json)
    except Exception:
        return {"raw": content_json}


def _extract_asr_text(content: dict) -> str:
    if not isinstance(content, dict):
        return ""
    normalized = content.get("normalized") or {}
    if isinstance(normalized, dict):
        text = normalized.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
    direct_text = content.get("text")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()
    raw_text = content.get("raw")
    if isinstance(raw_text, str) and raw_text.strip():
        return raw_text.strip()
    return ""


def _calc_asr_units(text: str) -> tuple[int, str]:
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    if cjk_chars:
        return len(cjk_chars), "char"
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)
    return len(words), "word"


def _decorate_asr_item(item: dict):
    if item.get("task_type") != "asr":
        return
    content = item.get("content")
    text = _extract_asr_text(content if isinstance(content, dict) else {})
    units, unit_type = _calc_asr_units(text)
    item["asr_text"] = text
    item["asr_units"] = units
    item["asr_unit_type"] = unit_type
    item["asr_vad_thres"] = ASR_VAD_THRES
    item["low_speech"] = units < ASR_VAD_THRES


def _serialize_result_row(row: models.PrelabelResult):
    item = {
        "id": row.id,
        "job_id": row.job_id,
        "audio_id": row.audio_id,
        "minute_ts": row.minute_ts,
        "task_type": row.task_type,
        "content": _parse_content(row.content_json),
        "created_at": row.created_at,
    }
    _decorate_asr_item(item)
    return item


def _resolve_audio_full_path(request: Request, file_path: str, runtime_audio_dir: str) -> str:
    if file_path.startswith("/"):
        full_path = file_path
    else:
        full_path = os.path.join(runtime_audio_dir, file_path)

    runtime_root = os.path.abspath(runtime_audio_dir)
    normalized = os.path.abspath(full_path)
    if not normalized.startswith(runtime_root):
        raise HTTPException(status_code=400, detail=t(request, "flash.audio_path_illegal"))
    return normalized


async def _trigger_prelabel_service(
    request: Request,
    db: Session,
    job: models.PrelabelJob,
    day_id: str,
    user_id: str,
    endpoint_path: str,
):
    configured_url = (os.getenv("PRELABEL_SERVICE_URL", "http://prelabel-service:8100") or "").strip()
    fallback_urls = ["http://prelabel-service:8100", "http://127.0.0.1:8100", "http://localhost:8100"]
    candidate_urls: list[str] = []
    if configured_url:
        candidate_urls.append(configured_url)
    for url in fallback_urls:
        if url not in candidate_urls:
            candidate_urls.append(url)

    last_error: Exception | None = None
    for base_url in candidate_urls:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    f"{base_url}{endpoint_path}",
                    json={"job_id": job.id, "day_id": day_id, "user_id": user_id},
                )
            if resp.status_code >= 400:
                raise RuntimeError(f"预标注服务响应错误: {resp.status_code}")

            data = resp.json() if resp.content else {}
            service_status = data.get("status") if isinstance(data, dict) else None
            if service_status in ("pending", "running", "done", "failed"):
                job.status = service_status
                db.commit()
            return
        except Exception as exc:
            last_error = exc

    try:
        now = int(time.time())
        job.status = "failed"
        job.started_at = now
        job.finished_at = now
        job.error_log = f"调用预标注服务失败: {str(last_error)[:500] if last_error else 'unknown error'}"
        db.commit()
    except Exception:
        db.rollback()

    raise HTTPException(status_code=502, detail=t(request, "flash.prelabel_service_unavailable"))


def _get_job_last_activity_ts(db: Session, job: models.PrelabelJob) -> int:
    base_ts = int(job.started_at or job.created_at or 0)

    latest_result_ts = db.query(func.max(models.PrelabelResult.created_at)).filter(
        models.PrelabelResult.job_id == job.id,
        models.PrelabelResult.userId == job.userId,
        models.PrelabelResult.day_id == job.day_id,
    ).scalar()
    if latest_result_ts:
        base_ts = max(base_ts, int(latest_result_ts))

    # 如果该日音频仍在持续更新（例如接收端每分钟新增/刷新），不应被视为超时。
    latest_queue_update_ts = db.query(func.max(models.AudioData.updated_at)).filter(
        models.AudioData.userId == job.userId,
        models.AudioData.date == job.day_id,
        models.AudioData.pre_label_status.in_(["queued", "running"]),
    ).scalar()
    if latest_queue_update_ts:
        base_ts = max(base_ts, int(latest_queue_update_ts))

    return base_ts


def _is_active_job_stale(db: Session, job: models.PrelabelJob) -> bool:
    now = int(time.time())
    base_ts = _get_job_last_activity_ts(db, job)
    if base_ts <= 0:
        return False
    return (now - int(base_ts)) > ACTIVE_JOB_STALE_SECONDS


def _mark_job_failed_if_stale(db: Session, job: models.PrelabelJob) -> bool:
    if job.status not in ("pending", "running"):
        return False
    if not _is_active_job_stale(db, job):
        return False

    now = int(time.time())
    job.status = "failed"
    job.finished_at = now
    if not job.started_at:
        job.started_at = job.created_at or now
    if not job.error_log:
        job.error_log = "任务超时未完成，已自动标记为失败，请重试"
    db.commit()
    return True


@router.post("/api/prelabel/create")
async def create_prelabel_job(
    request: Request,
    payload: dict = Body(...),
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    day_id = (payload.get("day_id") or "").strip()
    force = bool(payload.get("force", False))

    if not day_id or len(day_id) != 8 or not day_id.isdigit():
        raise HTTPException(status_code=400, detail=t(request, "flash.invalid_day_id"))

    has_data = db.query(models.AudioData.id).filter(
        models.AudioData.userId == user.userId,
        models.AudioData.date == day_id,
    ).first()
    if not has_data:
        raise HTTPException(status_code=404, detail=t(request, "flash.no_audio_for_day"))

    active_job = db.query(models.PrelabelJob).filter(
        models.PrelabelJob.userId == user.userId,
        models.PrelabelJob.day_id == day_id,
        models.PrelabelJob.status.in_(["pending", "running"]),
    ).order_by(models.PrelabelJob.created_at.desc()).first()
    if active_job:
        _mark_job_failed_if_stale(db, active_job)
        db.refresh(active_job)
    if active_job and active_job.status in ("pending", "running"):
        return {"job_id": active_job.id, "status": active_job.status, "reused": True}

    latest_done = db.query(models.PrelabelJob).filter(
        models.PrelabelJob.userId == user.userId,
        models.PrelabelJob.day_id == day_id,
        models.PrelabelJob.status == "done",
    ).order_by(models.PrelabelJob.created_at.desc()).first()
    if latest_done and not force and not ALLOW_REPEAT_PRELABEL:
        raise HTTPException(status_code=409, detail=t(request, "flash.prelabel_already_done"))

    now = int(time.time())
    job = models.PrelabelJob(
        userId=user.userId,
        day_id=day_id,
        status="pending",
        created_at=now,
        pipeline_version=os.getenv("PRELABEL_PIPELINE_VERSION", "mvp-asr-v1"),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    await _trigger_prelabel_service(request, db, job, day_id, user.userId, "/prelabel/run")

    db.refresh(job)
    return {
        "job_id": job.id,
        "status": job.status,
        "reused": False,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


@router.post("/api/prelabel/rerun-failed")
async def rerun_failed_minutes(
    request: Request,
    payload: dict = Body(...),
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    day_id = (payload.get("day_id") or "").strip()

    if not day_id or len(day_id) != 8 or not day_id.isdigit():
        raise HTTPException(status_code=400, detail=t(request, "flash.invalid_day_id"))

    active_job = db.query(models.PrelabelJob).filter(
        models.PrelabelJob.userId == user.userId,
        models.PrelabelJob.day_id == day_id,
        models.PrelabelJob.status.in_(["pending", "running"]),
    ).order_by(models.PrelabelJob.created_at.desc()).first()
    if active_job:
        _mark_job_failed_if_stale(db, active_job)
        db.refresh(active_job)
    if active_job and active_job.status in ("pending", "running"):
        return {"job_id": active_job.id, "status": active_job.status, "reused": True}

    failed_exists = db.query(models.AudioData.id).filter(
        models.AudioData.userId == user.userId,
        models.AudioData.date == day_id,
        models.AudioData.pre_label_status == "failed",
    ).first()
    if not failed_exists:
        raise HTTPException(status_code=409, detail=t(request, "flash.no_failed_segments"))

    now = int(time.time())
    base_version = os.getenv("PRELABEL_PIPELINE_VERSION", "mvp-asr-v1")
    job = models.PrelabelJob(
        userId=user.userId,
        day_id=day_id,
        status="pending",
        created_at=now,
        pipeline_version=f"{base_version}-rerun-failed",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    await _trigger_prelabel_service(request, db, job, day_id, user.userId, "/prelabel/rerun_failed")

    db.refresh(job)
    return {
        "job_id": job.id,
        "status": job.status,
        "reused": False,
        "mode": "failed_only",
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


@router.get("/api/prelabel/status/{job_id}")
async def get_prelabel_status(
    job_id: int,
    request: Request,
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    job = db.query(models.PrelabelJob).filter(
        models.PrelabelJob.id == job_id,
        models.PrelabelJob.userId == user.userId,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail=t(request, "flash.job_not_found"))
    _mark_job_failed_if_stale(db, job)
    db.refresh(job)
    return _serialize_job(job)


@router.get("/api/prelabel/results")
async def get_prelabel_results(
    day_id: str = Query(...),
    job_id: int | None = Query(default=None),
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    if job_id is None:
        job = db.query(models.PrelabelJob).filter(
            models.PrelabelJob.userId == user.userId,
            models.PrelabelJob.day_id == day_id,
            models.PrelabelJob.status == "done",
        ).order_by(models.PrelabelJob.created_at.desc()).first()
    else:
        job = db.query(models.PrelabelJob).filter(
            models.PrelabelJob.id == job_id,
            models.PrelabelJob.userId == user.userId,
            models.PrelabelJob.day_id == day_id,
        ).first()

    if not job:
        return {
            "job": None,
            "results": [],
            "asr_results": [],
            "sed_asc_har_results": [],
            "available_task_types": ["asr", "sed_asc_har"],
        }

    results = db.query(models.PrelabelResult).filter(
        and_(
            models.PrelabelResult.job_id == job.id,
            models.PrelabelResult.userId == user.userId,
            models.PrelabelResult.day_id == day_id,
        )
    ).order_by(models.PrelabelResult.audio_id.asc(), models.PrelabelResult.id.asc()).all()

    result_items = [_serialize_result_row(row) for row in results]
    asr_results = [item for item in result_items if item.get("task_type") == "asr"]
    sed_results = [item for item in result_items if item.get("task_type") == "sed_asc_har"]

    return {
        "job": _serialize_job(job),
        "results": result_items,
        "asr_results": asr_results,
        "sed_asc_har_results": sed_results,
        "available_task_types": ["asr", "sed_asc_har"],
        "asr_vad_thres": ASR_VAD_THRES,
    }


@router.get("/api/prelabel/jobs")
async def list_prelabel_jobs(
    day_id: str = Query(...),
    limit: int = Query(default=20, ge=1, le=200),
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    jobs = db.query(models.PrelabelJob).filter(
        models.PrelabelJob.userId == user.userId,
        models.PrelabelJob.day_id == day_id,
    ).order_by(models.PrelabelJob.created_at.desc()).limit(limit).all()
    return {
        "jobs": [_serialize_job(job) for job in jobs],
        "allow_repeat": ALLOW_REPEAT_PRELABEL,
    }


@router.post("/api/prelabel/export")
async def export_prelabel_zip(
    request: Request,
    payload: dict = Body(...),
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    day_id = (payload.get("day_id") or "").strip()
    if not day_id or len(day_id) != 8 or not day_id.isdigit():
        raise HTTPException(status_code=400, detail=t(request, "flash.invalid_day_id"))

    raw_audio_ids = payload.get("audio_ids") or []
    if not isinstance(raw_audio_ids, list) or not raw_audio_ids:
        raise HTTPException(status_code=400, detail=t(request, "flash.choose_one_audio"))

    try:
        audio_ids = [int(v) for v in raw_audio_ids]
    except Exception:
        raise HTTPException(status_code=400, detail=t(request, "flash.audio_ids_invalid"))

    audio_ids = list(dict.fromkeys(audio_ids))

    job_id = payload.get("job_id")
    if job_id is None:
        job = db.query(models.PrelabelJob).filter(
            models.PrelabelJob.userId == user.userId,
            models.PrelabelJob.day_id == day_id,
            models.PrelabelJob.status == "done",
        ).order_by(models.PrelabelJob.created_at.desc()).first()
    else:
        try:
            parsed_job_id = int(job_id)
        except Exception:
            raise HTTPException(status_code=400, detail=t(request, "flash.job_id_invalid"))

        job = db.query(models.PrelabelJob).filter(
            models.PrelabelJob.id == parsed_job_id,
            models.PrelabelJob.userId == user.userId,
            models.PrelabelJob.day_id == day_id,
        ).first()

    if not job:
        raise HTTPException(status_code=404, detail=t(request, "flash.export_job_not_found"))

    audio_rows = db.query(models.AudioData).filter(
        models.AudioData.userId == user.userId,
        models.AudioData.date == day_id,
        models.AudioData.id.in_(audio_ids),
    ).order_by(models.AudioData.id.asc()).all()

    if len(audio_rows) != len(audio_ids):
        raise HTTPException(status_code=400, detail=t(request, "flash.invalid_audio_or_permission"))

    results = db.query(models.PrelabelResult).filter(
        models.PrelabelResult.userId == user.userId,
        models.PrelabelResult.day_id == day_id,
        models.PrelabelResult.job_id == job.id,
        models.PrelabelResult.audio_id.in_(audio_ids),
    ).order_by(
        models.PrelabelResult.audio_id.asc(),
        models.PrelabelResult.id.asc(),
    ).all()

    results_by_audio: dict[int, list[models.PrelabelResult]] = {}
    for row in results:
        key = int(row.audio_id) if row.audio_id is not None else -1
        if key not in results_by_audio:
            results_by_audio[key] = []
        results_by_audio[key].append(row)

    runtime_audio_dir = os.environ.get("RUNTIME_AUDIO_DIR", "/runtime/data/audio")

    used_names: dict[str, int] = {}
    export_meta: list[dict] = []
    for audio in audio_rows:
        src_full_path = _resolve_audio_full_path(request, audio.file_path, runtime_audio_dir)
        if not os.path.exists(src_full_path):
            raise HTTPException(status_code=404, detail=t(request, "flash.audio_file_not_found", audio_id=audio.id))

        original_name = os.path.basename(src_full_path) or f"audio_{audio.id}.opus"
        name_root, name_ext = os.path.splitext(original_name)
        duplicate_index = used_names.get(original_name, 0)
        if duplicate_index == 0:
            zip_name = original_name
        else:
            zip_name = f"{name_root}_{duplicate_index}{name_ext}"
        used_names[original_name] = duplicate_index + 1

        export_meta.append({
            "audio": audio,
            "src_full_path": src_full_path,
            "zip_name": zip_name,
        })

    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerow([
        "audio_id",
        "relative_path",
        "task_type",
        "prelabel_result",
    ])

    for item in export_meta:
        audio = item["audio"]
        relative_path = f"./{item['zip_name']}"
        item_results = results_by_audio.get(int(audio.id), [])
        if not item_results:
            csv_writer.writerow([audio.id, relative_path, "", ""])
            continue

        for r in item_results:
            parsed = _parse_content(r.content_json)
            csv_writer.writerow([
                audio.id,
                relative_path,
                r.task_type,
                json.dumps(parsed, ensure_ascii=False),
            ])

    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in export_meta:
            zf.write(item["src_full_path"], arcname=item["zip_name"])
        zf.writestr("prelabel_results.csv", csv_buffer.getvalue().encode("utf-8-sig"))

    zip_bytes.seek(0)
    filename = f"prelabel_export_{day_id}_job{job.id}.zip"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(zip_bytes, media_type="application/zip", headers=headers)


@router.get("/tasks/{day_id}/prelabel", response_class=HTMLResponse)
async def prelabel_result_page(
    day_id: str,
    request: Request,
    job_id: int | None = Query(default=None),
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    jobs_history = db.query(models.PrelabelJob).filter(
        models.PrelabelJob.userId == user.userId,
        models.PrelabelJob.day_id == day_id,
    ).order_by(models.PrelabelJob.created_at.desc()).all()

    latest_job = jobs_history[0] if jobs_history else None

    selected_job = None
    if job_id is not None:
        selected_job = db.query(models.PrelabelJob).filter(
            models.PrelabelJob.id == job_id,
            models.PrelabelJob.userId == user.userId,
            models.PrelabelJob.day_id == day_id,
        ).first()
    if selected_job is None:
        selected_job = latest_job

    result_rows = []
    asr_results = []
    sed_results = []
    audio_map = {}
    low_speech_count = 0

    if selected_job and selected_job.status == "done":
        result_rows = db.query(models.PrelabelResult).filter(
            models.PrelabelResult.job_id == selected_job.id,
            models.PrelabelResult.userId == user.userId,
            models.PrelabelResult.day_id == day_id,
        ).order_by(models.PrelabelResult.audio_id.asc(), models.PrelabelResult.id.asc()).all()

    audio_ids = [int(row.audio_id) for row in result_rows if row.audio_id is not None]
    if audio_ids:
        audio_rows = db.query(models.AudioData).filter(
            models.AudioData.userId == user.userId,
            models.AudioData.id.in_(audio_ids),
        ).all()
        audio_map = {
            int(audio.id): {
                "start_ts": audio.start_ts,
                "duration_sec": audio.duration_sec,
            }
            for audio in audio_rows
        }

    for row in result_rows:
        data = {
            "audio_id": row.audio_id,
            "minute_ts": row.minute_ts,
            "task_type": row.task_type,
            "content": _parse_content(row.content_json),
            "audio_start_ts": audio_map.get(int(row.audio_id), {}).get("start_ts") if row.audio_id is not None else None,
            "duration_sec": audio_map.get(int(row.audio_id), {}).get("duration_sec") if row.audio_id is not None else None,
        }
        _decorate_asr_item(data)
        if row.task_type == "asr":
            asr_results.append(data)
            if data.get("low_speech"):
                low_speech_count += 1
        elif row.task_type == "sed_asc_har":
            sed_results.append(data)

    return templates.TemplateResponse("tasks/prelabel.html", {
        "request": request,
        "day_id": day_id,
        "job": selected_job,
        "latest_job": latest_job,
        "jobs_history": jobs_history,
        "allow_repeat": ALLOW_REPEAT_PRELABEL,
        "selected_job_id": selected_job.id if selected_job else None,
        "asr_results": asr_results,
        "sed_results": sed_results,
        "asr_vad_thres": ASR_VAD_THRES,
        "low_speech_count": low_speech_count,
    })

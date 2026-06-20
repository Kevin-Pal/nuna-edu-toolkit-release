from fastapi import APIRouter, Request, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from fastapi import Body
from .. import models
from ..database import get_db
from ..dependencies import templates, flash
from ..i18n import t
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import unquote
from typing import cast
import os
import json


def _extract_asr_text_from_content_json(content_json: str | None) -> str:
    if not content_json:
        return ""

    try:
        content = json.loads(content_json)
    except Exception:
        return ""

    if not isinstance(content, dict):
        return ""

    normalized = content.get("normalized")
    if isinstance(normalized, dict):
        text = normalized.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

    for key in ("text", "raw"):
        val = content.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    return ""

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("userId")
    if not user_id:
        return None
    user = db.query(models.User).filter(models.User.userId == user_id).first()
    return user


def require_login(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_302_FOUND, headers={"Location": "/auth/login"})
    return user


@router.get("", response_class=HTMLResponse)
async def task_list(
    request: Request,
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    latest_prelabel_by_day = {}
    prelabel_jobs = db.query(models.PrelabelJob).filter(
        models.PrelabelJob.userId == user.userId
    ).order_by(
        models.PrelabelJob.created_at.desc()
    ).all()
    for job in prelabel_jobs:
        if job.day_id not in latest_prelabel_by_day:
            latest_prelabel_by_day[job.day_id] = job

    stats = db.query(
        models.AudioData.date,
        func.count(models.AudioData.id).label("total"),
        func.sum(case((models.AudioData.label_status != 'unlabeled', 1), else_=0)).label("labeled")
    ).filter(
        models.AudioData.userId == user.userId
    ).group_by(
        models.AudioData.date
    ).order_by(
        models.AudioData.date.desc()
    ).all()

    tasks_data = []
    for row in stats:
        progress = 0
        labeled = row.labeled or 0
        if row.total > 0:
            progress = round((labeled / row.total) * 100, 1)

        latest_prelabel = latest_prelabel_by_day.get(row.date)

        tasks_data.append({
            "date": row.date,
            "total_segments": row.total,
            "duration_minutes": row.total,
            "labeled_count": labeled,
            "progress": int(progress),
            "prelabel_status": latest_prelabel.status if latest_prelabel else "not_run",
            "prelabel_job_id": latest_prelabel.id if latest_prelabel else None,
            "prelabel_started_at": latest_prelabel.started_at if latest_prelabel else None,
            "prelabel_finished_at": latest_prelabel.finished_at if latest_prelabel else None,
            "prelabel_has_history": latest_prelabel is not None,
        })

    return templates.TemplateResponse("tasks/list.html", {
        "request": request,
        "tasks": tasks_data,
        "sync_status": user.last_sync_status,
        "sync_msg": user.last_sync_msg,
        "last_sync_ts": int(getattr(user, "last_sync_time") or 0)
    })


@router.post("/sync")
async def trigger_sync(request: Request, user: models.User = Depends(require_login)):
    customer_server_url = os.getenv("CUSTOMER_SERVER_URL", "http://localhost:9000/")
    flash(
        request,
        t(request, "flash.manual_sync_disabled", url=customer_server_url),
        "info",
    )
    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)


@router.get("/{date}", response_class=HTMLResponse)
async def task_detail(date: str, request: Request, user: models.User = Depends(require_login), db: Session = Depends(get_db)):
    segments_query = db.query(models.AudioData).filter(
        models.AudioData.userId == user.userId,
        models.AudioData.date == date
    ).order_by(models.AudioData.start_ts.asc()).all()

    total_segments = len(segments_query)

    blocks = db.query(models.AnnotationBlock).filter(
        models.AnnotationBlock.userId == user.userId,
        models.AnnotationBlock.date == date
    ).all()

    latest_prelabel = db.query(models.PrelabelJob).filter(
        models.PrelabelJob.userId == user.userId,
        models.PrelabelJob.day_id == date,
    ).order_by(models.PrelabelJob.created_at.desc()).first()

    latest_asr_text_by_audio_id: dict[int, str] = {}
    if latest_prelabel:
        asr_rows = db.query(models.PrelabelResult).filter(
            models.PrelabelResult.job_id == latest_prelabel.id,
            models.PrelabelResult.userId == user.userId,
            models.PrelabelResult.day_id == date,
            models.PrelabelResult.task_type == "asr",
        ).order_by(models.PrelabelResult.id.asc()).all()

        for row in asr_rows:
            audio_id = cast(int | None, row.audio_id)
            if audio_id is None:
                continue
            latest_asr_text_by_audio_id[audio_id] = _extract_asr_text_from_content_json(row.content_json)

    block_ranges = []
    for block in blocks:
        block_ranges.append((block.start_audio_id, block.end_audio_id, block))

    def find_block(seg_id: int):
        for start_id, end_id, blk in block_ranges:
            if start_id <= seg_id <= end_id:
                return blk
        return None

    hours_map = {}
    tz_cookie = request.cookies.get("tz")
    tzinfo = None
    if tz_cookie:
        try:
            tzinfo = ZoneInfo(unquote(tz_cookie))
        except Exception:
            tzinfo = None
    if tzinfo is None:
        tzinfo = timezone.utc

    try:
        page_utc_start = datetime.strptime(date, "%Y%m%d").replace(tzinfo=timezone.utc)
    except Exception:
        page_utc_start = datetime.fromtimestamp(0, tz=timezone.utc)
    page_local_base_date = page_utc_start.astimezone(tzinfo).date()

    def day_prefix(offset: int) -> str:
        if offset > 0:
            return t(request, "detail.next_day")
        if offset < 0:
            return t(request, "detail.prev_day")
        return ""

    for seg in segments_query:
        seg_start_ts = cast(int, seg.start_ts)
        seg_id = cast(int, seg.id)

        dt = datetime.fromtimestamp(seg_start_ts, tz=tzinfo)
        local_day_offset = (dt.date() - page_local_base_date).days
        local_prefix = day_prefix(local_day_offset)

        hour_key = dt.strftime("%H")
        hour_bucket_key = f"{local_day_offset}:{hour_key}"
        minute = dt.minute
        quarter_idx = minute // 15
        start_min = quarter_idx * 15
        start_dt = dt.replace(minute=start_min, second=0, microsecond=0)
        end_dt = start_dt + timedelta(minutes=15)
        quarter_label = f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
        if local_prefix:
            quarter_label = f"{local_prefix} {quarter_label}"

        block_obj = find_block(seg_id)

        seg_data = {
            "id": seg_id,
            "start_ts": seg_start_ts,
            "label_status": seg.label_status,
            "block": block_obj,
            "local_day_prefix": local_prefix,
            "latest_asr_text": latest_asr_text_by_audio_id.get(seg_id, ""),
        }

        hour_bucket = hours_map.setdefault(hour_bucket_key, {
            "hour": hour_key,
            "day_offset": local_day_offset,
            "day_prefix": local_prefix,
            "quarters": {},
        })
        quarter_bucket = hour_bucket["quarters"].setdefault(quarter_idx, {
            "quarter": quarter_idx,
            "label": quarter_label,
            "segments": []
        })
        quarter_bucket["segments"].append(seg_data)

    hours = []
    for hour_bucket in hours_map.values():
        quarter_map = hour_bucket["quarters"]
        quarters_list = list(quarter_map.values())
        hour_title = f"{hour_bucket['hour']}:00"
        if hour_bucket["day_prefix"]:
            hour_title = f"{hour_bucket['day_prefix']} {hour_title}"
        hour_id = f"h_{hour_bucket['day_offset']}_{hour_bucket['hour']}"
        hours.append({
            "hour": hour_bucket["hour"],
            "hour_id": hour_id,
            "hour_title": hour_title,
            "quarters": quarters_list,
            "segment_count": sum(len(q["segments"]) for q in quarters_list),
        })

    return templates.TemplateResponse("tasks/detail.html", {
        "request": request,
        "date": date,
        "total_segments": total_segments,
        "hours": hours,
        "prelabel_job": latest_prelabel,
    })


@router.post("/delete")
async def delete_segments(
    request: Request,
    payload: dict = Body(...),
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    ids_raw = payload.get("ids") or []
    if not isinstance(ids_raw, list) or not ids_raw:
        raise HTTPException(status_code=400, detail=t(request, "flash.no_segment_selected"))

    try:
        ids = [int(i) for i in ids_raw]
    except Exception:
        raise HTTPException(status_code=400, detail=t(request, "flash.segment_id_invalid"))

    segments = db.query(models.AudioData).filter(
        models.AudioData.userId == user.userId,
        models.AudioData.id.in_(ids)
    ).all()

    if len(segments) != len(ids):
        raise HTTPException(status_code=400, detail=t(request, "flash.invalid_or_no_permission_segment"))

    for seg in segments:
        block = db.query(models.AnnotationBlock).filter(
            models.AnnotationBlock.userId == user.userId,
            models.AnnotationBlock.start_audio_id <= seg.id,
            models.AnnotationBlock.end_audio_id >= seg.id,
        ).first()
        if block:
            raise HTTPException(
                status_code=400,
                detail=t(request, "flash.segment_in_block", seg_id=seg.id, block_id=block.id),
            )

        point = db.query(models.AnnotationPoint).filter(
            models.AnnotationPoint.userId == user.userId,
            models.AnnotationPoint.start_audio_id <= seg.id,
            models.AnnotationPoint.end_audio_id >= seg.id,
        ).first()
        if point:
            raise HTTPException(
                status_code=400,
                detail=t(request, "flash.segment_in_point", seg_id=seg.id, point_id=point.id),
            )

    runtime_audio_dir = os.getenv("RUNTIME_AUDIO_DIR", "/runtime/data/audio") or "/runtime/data/audio"
    files_removed = 0

    for seg in segments:
        full_path = os.path.join(runtime_audio_dir, str(seg.file_path))
        try:
            os.remove(full_path)
            files_removed += 1
        except FileNotFoundError:
            pass
        except Exception as e:
            raise HTTPException(status_code=500, detail=t(request, "flash.file_delete_failed", reason=str(e)[:120]))

        db.delete(seg)

    db.commit()

    return {"message": t(request, "flash.delete_success"), "deleted": len(segments), "files_removed": files_removed}

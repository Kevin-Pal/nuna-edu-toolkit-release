from fastapi import APIRouter, Request, Depends, status, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..dependencies import flash
from ..i18n import t
from .tasks import require_login

router = APIRouter(prefix="/points", tags=["points"])


@router.post("")
async def create_point(
    request: Request,
    block_id: int = Form(...),
    start_audio_id: int = Form(...),
    end_audio_id: int = Form(...),
    pe_type: str = Form(...),
    env_subject: str = Form(None),
    env_predicate: str = Form(None),
    act_adv: str = Form(None),
    act_verb: str = Form(None),
    pe_note: str = Form(None),
    va_grid: str = Form(...),  # format: "valence,arousal"
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    redirect_url = f"/blocks/{block_id}"

    try:
        emo_valence, emo_arousal = va_grid.split(",")
    except Exception:
        flash(request, t(request, "flash.emotion_invalid"), "danger")
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    block = db.query(models.AnnotationBlock).filter(
        models.AnnotationBlock.id == block_id,
        models.AnnotationBlock.userId == user.userId,
    ).first()

    if not block:
        flash(request, t(request, "flash.block_not_found"), "danger")
        return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)

    if start_audio_id > end_audio_id:
        flash(request, t(request, "flash.start_gt_end"), "danger")
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    if start_audio_id < block.start_audio_id or end_audio_id > block.end_audio_id:
        flash(request, t(request, "flash.point_range"), "danger")
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    expected_count = end_audio_id - start_audio_id + 1
    segments = db.query(models.AudioData).filter(
        models.AudioData.userId == user.userId,
        models.AudioData.date == block.date,
        models.AudioData.id >= start_audio_id,
        models.AudioData.id <= end_audio_id,
    ).order_by(models.AudioData.id.asc()).all()

    if len(segments) != expected_count:
        flash(request, t(request, "flash.segment_not_continuous"), "danger")
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    pe_type_clean = (pe_type or "").strip()
    if pe_type_clean not in ["env_fluctuation", "personal_action"]:
        flash(request, t(request, "flash.select_point_type"), "danger")
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    if pe_type_clean == "env_fluctuation":
        if not env_subject or not env_predicate:
            flash(request, t(request, "flash.env_need_subject_predicate"), "danger")
            return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        act_adv = None
        act_verb = None
    else:
        if not act_adv or not act_verb:
            flash(request, t(request, "flash.act_need_adv_verb"), "danger")
            return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        env_subject = None
        env_predicate = None

    point = models.AnnotationPoint(
        userId=user.userId,
        block_id=block.id,
        start_audio_id=start_audio_id,
        end_audio_id=end_audio_id,
        segment_count=expected_count,
        pe_type=pe_type_clean,
        env_subject=env_subject,
        env_predicate=env_predicate,
        act_adv=act_adv,
        act_verb=act_verb,
        pe_note=pe_note,
        emo_valence=emo_valence,
        emo_arousal=emo_arousal,
    )

    db.add(point)
    db.commit()

    flash(request, t(request, "flash.point_created"), "success")
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

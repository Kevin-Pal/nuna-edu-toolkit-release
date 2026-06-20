from fastapi import APIRouter, Request, Depends, status, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from .tasks import require_login
from ..dependencies import flash, templates
from ..i18n import t
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/blocks", tags=["blocks"])

@router.post("")
async def create_block(
    request: Request,
    date: str = Form(...),
    start_audio_id: int = Form(...),
    end_audio_id: int = Form(...),
    scene_adj: str = Form(...),
    scene_noun: str = Form(...),
    scene_note: str = Form(None),
    be_adv: str = Form(...),
    be_verb: str = Form(...),
    be_note: str = Form(None),
    va_grid: str = Form(...), # format: "valence,arousal" e.g. "high,low"
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db)
):
    # Parse VA
    try:
        emo_valence, emo_arousal = va_grid.split(',')
    except:
        flash(request, t(request, "flash.emotion_invalid"), "danger")
        return RedirectResponse(url=f"/tasks/{date}", status_code=status.HTTP_302_FOUND)

    # 1. Validation: Range
    if start_audio_id > end_audio_id:
        flash(request, t(request, "flash.start_gt_end"), "danger")
        return RedirectResponse(url=f"/tasks/{date}", status_code=status.HTTP_302_FOUND)

    # 2. Fetch segments in range
    # We assume IDs are sequential for the same user/date. 
    # Proper check: Count(id) where id between start and end == end - start + 1
    segments = db.query(models.AudioData).filter(
        models.AudioData.userId == user.userId,
        models.AudioData.id >= start_audio_id,
        models.AudioData.id <= end_audio_id
    ).all()
    
    expected_count = end_audio_id - start_audio_id + 1
    if len(segments) != expected_count:
        flash(request, t(request, "flash.segment_not_continuous"), "danger")
        return RedirectResponse(url=f"/tasks/{date}", status_code=status.HTTP_302_FOUND)
        
    # 3. Validation: Overlap
    for seg in segments:
        if seg.label_status != "unlabeled":
             flash(request, t(request, "flash.segment_labeled", id=seg.id), "danger")
             return RedirectResponse(url=f"/tasks/{date}", status_code=status.HTTP_302_FOUND)

    # 4. Create Block
    new_block = models.AnnotationBlock(
        userId=user.userId,
        date=date,
        start_audio_id=start_audio_id,
        end_audio_id=end_audio_id,
        segment_count=expected_count,
        scene_adj=scene_adj,
        scene_noun=scene_noun,
        scene_note=scene_note,
        be_adv=be_adv,
        be_verb=be_verb,
        be_note=be_note,
        emo_valence=emo_valence,
        emo_arousal=emo_arousal
    )
    db.add(new_block)
    
    # 5. Update Segments status
    for seg in segments:
        seg.label_status = "labeled"
    
    db.commit()
    db.refresh(new_block)
    
    flash(request, t(request, "flash.block_created"), "success")
    return RedirectResponse(url=f"/blocks/{new_block.id}", status_code=status.HTTP_302_FOUND)

@router.get("/{block_id}", response_class=HTMLResponse)
async def view_block(
    block_id: int,
    request: Request,
    user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    block = db.query(models.AnnotationBlock).filter(
        models.AnnotationBlock.id == block_id,
        models.AnnotationBlock.userId == user.userId,
    ).first()

    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t(request, "flash.block_not_found"))

    segments = db.query(models.AudioData).filter(
        models.AudioData.userId == user.userId,
        models.AudioData.id >= block.start_audio_id,
        models.AudioData.id <= block.end_audio_id,
    ).order_by(models.AudioData.start_ts.asc()).all()

    points = db.query(models.AnnotationPoint).filter(
        models.AnnotationPoint.userId == user.userId,
        models.AnnotationPoint.block_id == block.id,
    ).order_by(models.AnnotationPoint.start_audio_id.asc()).all()

    # Map segment id -> list of points covering it (for badge rendering)
    seg_point_map = {}
    for pt in points:
        for seg_id in range(pt.start_audio_id, pt.end_audio_id + 1):
            seg_point_map.setdefault(seg_id, []).append(pt)

    segments_data = []
    for seg in segments:
        segments_data.append({
            "id": seg.id,
            "start_ts": seg.start_ts,
            "points": seg_point_map.get(seg.id, []),
        })

    return templates.TemplateResponse("blocks/detail.html", {
        "request": request,
        "block": block,
        "segments": segments_data,
        "points": points,
    })


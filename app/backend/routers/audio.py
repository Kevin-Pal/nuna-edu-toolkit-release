from fastapi import APIRouter, Request, Depends, status, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from .tasks import require_login
import os

router = APIRouter(prefix="/audio", tags=["audio"])

@router.get("/{audio_id}/stream")
async def stream_audio(audio_id: int, request: Request, user: models.User = Depends(require_login), db: Session = Depends(get_db)):
    # 1. Verify ownership
    audio = db.query(models.AudioData).filter(models.AudioData.id == audio_id, models.AudioData.userId == user.userId).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    # 2. Resolve the on-disk path (stored relative to the audio root, or absolute).
    runtime_audio_dir = os.environ.get("RUNTIME_AUDIO_DIR", "/runtime/data/audio")
    runtime_root = os.path.abspath(runtime_audio_dir)
    if audio.file_path.startswith("/"):
        full_path = audio.file_path
    else:
        full_path = os.path.join(runtime_audio_dir, audio.file_path)

    # Confine to the audio root — reject any path traversal.
    full_path = os.path.abspath(full_path)
    if os.path.commonpath([full_path, runtime_root]) != runtime_root:
        raise HTTPException(status_code=400, detail="Invalid audio path")

    if not os.path.exists(full_path):
        return Response(status_code=404, content="File not found on disk")

    return FileResponse(full_path, media_type="audio/mpeg", filename=f"segment_{audio_id}.mp3")

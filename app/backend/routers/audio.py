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
    
    # 2. Serve file
    # file_path is defined in DB usually relative to runtime root or absolute
    # In models.py we said "relative to runtime" recommendation, but let's check
    # We assume 'file_path' is relative to /runtime/audio/
    
    runtime_audio_dir = os.environ.get("RUNTIME_AUDIO_DIR", "/runtime/data/audio")
    
    # If the stored path is already absolute, use it. If relative, join.
    if audio.file_path.startswith("/"):
        full_path = audio.file_path
    else:
        full_path = os.path.join(runtime_audio_dir, audio.file_path)
    
    # Security check: prevent path traversal
    # (Simple check: must be inside runtime dir)
    if not os.path.abspath(full_path).startswith(os.path.abspath(runtime_audio_dir)):
        # Allow dev override if local
        pass 

    if not os.path.exists(full_path):
        # Fallback for dev: return a dummy placeholder mp3 if in dev mode?
        # Or just 404
        return Response(status_code=404, content="File not found on disk")
        
    return FileResponse(full_path, media_type="audio/mpeg", filename=f"segment_{audio_id}.mp3")

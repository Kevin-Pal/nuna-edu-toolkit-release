from datetime import datetime, timezone
import json
import os

from fastapi import FastAPI, File, HTTPException, UploadFile

from . import models
from .database import Base, SessionLocal, engine


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nuna Audio Receiver")


def _getenv_clean(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name)
    if val is None:
        return default
    val = val.strip()
    if len(val) >= 2 and ((val[0] == "'" and val[-1] == "'") or (val[0] == '"' and val[-1] == '"')):
        val = val[1:-1].strip()
    return val


def _parse_unix_ts(raw: object) -> int | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None

    # Numeric (int/float) unix timestamp
    try:
        numeric = float(value)
        ts = int(numeric)
        if ts >= 1_000_000_000_000:
            return ts // 1000
        return ts
    except Exception:
        pass

    # Fallback: ISO datetime string
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


@app.post("/thingx/api/file/upload/audio")
async def upload_audio(
    file: UploadFile = File(...),
    metadata: UploadFile = File(...),
):
    try:
        metadata_bytes = await metadata.read()
        metadata_str = metadata_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Metadata is not valid UTF-8 text")

    try:
        meta = json.loads(metadata_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Metadata is not valid JSON")

    required = ["userId", "name", "startTime", "endTime", "mac", "size"]
    missing = [field for field in required if field not in meta]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing field: {', '.join(missing)}")

    user_id = str(meta.get("userId", "")).strip()
    file_name = os.path.basename(str(meta.get("name", "")).strip())
    if not user_id or not file_name:
        raise HTTPException(status_code=400, detail="userId and name are required")

    # Keep compatible with existing uploader behavior: tolerate non-standard time formats.
    start_ts = _parse_unix_ts(meta.get("startTime"))
    end_ts = _parse_unix_ts(meta.get("endTime"))
    if start_ts is None:
        # Fallback to current time instead of failing request.
        start_ts = int(datetime.now(timezone.utc).timestamp())
    if end_ts is None:
        end_ts = start_ts + 60

    runtime_audio_dir = _getenv_clean("RUNTIME_AUDIO_DIR", "/runtime/data/audio") or "/runtime/data/audio"
    date_str = datetime.fromtimestamp(start_ts, tz=timezone.utc).strftime("%Y%m%d")
    rel_path = os.path.join(user_id, date_str, file_name)
    full_path = os.path.join(runtime_audio_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    audio_content = await file.read()
    if not audio_content:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    db = SessionLocal()
    try:
        existing = db.query(models.AudioData).filter(
            models.AudioData.userId == user_id,
            models.AudioData.start_ts == start_ts,
        ).first()

        with open(full_path, "wb") as f:
            f.write(audio_content)

        pre_label_provider = (_getenv_clean("ASR_PROVIDER", "none") or "none").strip().lower()

        if existing:
            setattr(existing, "file_path", rel_path)
            setattr(existing, "date", date_str)
            setattr(existing, "duration_sec", 60)
            setattr(existing, "pre_label_status", "empty" if pre_label_provider == "none" else "queued")
        else:
            audio = models.AudioData(
                userId=user_id,
                file_path=rel_path,
                date=date_str,
                start_ts=start_ts,
                duration_sec=60,
                pre_label_status="empty" if pre_label_provider == "none" else "queued",
                label_status="unlabeled",
            )
            db.add(audio)

        user = db.query(models.User).filter(models.User.userId == user_id).first()
        if user:
            setattr(user, "last_sync_time", int(datetime.now(timezone.utc).timestamp()))
            setattr(user, "last_sync_status", "success")
            setattr(user, "last_sync_msg", "已接收新音频")

        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)[:120]}")
    finally:
        db.close()

    return {"code": 200, "message": "success", "data": None}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "server_port": 9000,
    }

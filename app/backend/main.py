from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from . import models
from .routers import auth, index, tasks, blocks, audio, points, prelabel
from starlette.middleware.sessions import SessionMiddleware
import os
import time

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nuna Audio Lab App")
app.state.asset_version = os.getenv("ASSET_VERSION", str(int(time.time())))

# Add Session Middleware
session_secret = os.getenv("SESSION_SECRET", "dev_secret")
app.add_middleware(SessionMiddleware, secret_key=session_secret)

# Mount Static Files
static_dir = "/app/frontend/static"
if not os.path.exists(static_dir):
    # Fallback for local development if running outside docker but with code
    local_static = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "static")
    if os.path.exists(local_static):
        static_dir = local_static

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
app.include_router(index.router)
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(blocks.router)
app.include_router(points.router)
app.include_router(audio.router)
app.include_router(prelabel.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Nuna Audio Lab App is running"}

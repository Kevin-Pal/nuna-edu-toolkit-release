from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .. import models
from ..database import get_db
from ..dependencies import templates, flash
from ..i18n import t
import time
import os

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def check_uploaded_audio_exists(db: Session, user_id: str) -> bool:
    segment = db.query(models.AudioData.id).filter(models.AudioData.userId == user_id).first()
    return segment is not None

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.userId == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": t(request, "flash.login_failed")
        }, status_code=status.HTTP_400_BAD_REQUEST)
    
    # Simple Session Management
    request.session["userId"] = user.userId
    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    userId: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    errors = []
    
    # Enforce password length limits compatible with bcrypt (max 72 bytes)
    if len(password) < 8 or len(password) > 72:
        errors.append(t(request, "flash.password_len"))

    if password != confirm_password:
        errors.append(t(request, "flash.password_mismatch"))
    
    # 1. Check if user already exists
    existing_user = db.query(models.User).filter(models.User.userId == userId).first()
    if existing_user:
        errors.append(t(request, "flash.user_exists"))
    
    # 2. Check whether this user has uploaded valid audio data to current server
    if not check_uploaded_audio_exists(db, userId):
        customer_server_url = os.getenv("CUSTOMER_SERVER_URL", "http://localhost:9000/")
        errors.append(t(request, "flash.no_audio", url=customer_server_url))
        
    if errors:
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": " | ".join(errors)
        }, status_code=status.HTTP_400_BAD_REQUEST)
    
    initial_sync_time = int(time.time())
    
    try:
        hashed_pw = get_password_hash(password)
    except ValueError:
        # Bcrypt raises for inputs over 72 bytes; we already guard by length, but keep safe
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": t(request, "flash.password_len")
        }, status_code=status.HTTP_400_BAD_REQUEST)

    new_user = models.User(
        userId=userId,
        email=email,
        password_hash=hashed_pw,
        last_sync_time=initial_sync_time
    )
    db.add(new_user)
    db.commit()
    
    flash(request, t(request, "flash.register_success"), "success")
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

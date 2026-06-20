from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from ..dependencies import templates, flash
from ..i18n import set_lang_cookie

router = APIRouter(tags=["pages"])

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if "userId" in request.session:
        return RedirectResponse(url="/tasks")
    return RedirectResponse(url="/auth/login")


@router.get("/set-lang")
async def set_lang(request: Request, lang: str, next: str = "/"):
    response = RedirectResponse(url=next)
    set_lang_cookie(response, lang)
    return response

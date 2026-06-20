from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from .i18n import t, resolve_lang, catalog_for

# Create a place to store templates, to be initialized in main.py or here
# We'll use a common dependency or just init it here if path is fixed
import os
# __file__ is /app/backend/dependencies.py inside container; go up one to /app/backend, two to /app.
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "templates")
templates = Jinja2Templates(directory=templates_dir)

# Add flash message support to Jinja2
def flash(request: Request, message: str, category: str = "primary"):
    if "_messages" not in request.session:
        request.session["_messages"] = []
    request.session["_messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request, with_categories: bool = False):
    messages = request.session.pop("_messages") if "_messages" in request.session else []
    if with_categories:
        return [(m.get("category"), m.get("message")) for m in messages]
    return [m.get("message") for m in messages]

templates.env.globals['get_flashed_messages'] = get_flashed_messages
templates.env.globals['flash'] = flash
templates.env.globals['t'] = t
templates.env.globals['current_lang'] = resolve_lang
templates.env.globals['i18n_catalog'] = catalog_for

import base64
import json
import logging
import os
import time
from contextlib import contextmanager

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from starlette.middleware.base import BaseHTTPMiddleware

from components.sidebar import create_sidebar
from pages.agenda import agenda_page
from pages.home import home_page
from pages.login import login_page
from pages.persons import persons_page
from pages.preset import preset_page
from pages.pricing import pricing_page
from pages.settings import settings_page

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)

# Same matrix as the sidebar and role_conf.md. The backend still enforces everything; this is defense in depth.
ROUTE_ROLES: dict[str, set[str]] = {
    "/persons": {"admin", "manager", "secretary"},
    "/pricing": {"admin", "manager", "secretary", "doctor", "assistant", "employee"},
    "/preset": {"admin", "manager", "secretary", "doctor"},
    "/settings": {"admin", "manager"},
}


def role_allows(path: str, role: str) -> bool:
    for prefix, roles in ROUTE_ROLES.items():
        if path == prefix or path.startswith(prefix + "/"):
            return role in roles
    return True


def is_token_expired(token: str | None) -> bool:
    """Decodes the JWT payload natively to check the expiration timestamp."""
    if not token:
        return True
    try:
        payload_part = token.split(".")[1]
        padded = payload_part + "=" * (-len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return payload.get("exp", 0) < time.time()
    except Exception:
        return True


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = app.storage.user.get("token")

        if app.storage.user.get("authenticated", False) and is_token_expired(token):
            app.storage.user["authenticated"] = False
            app.storage.user["token"] = None

        path = request.url.path
        if not app.storage.user.get("authenticated", False):
            if path not in ["/login"] and not path.startswith("/_nicegui"):
                return RedirectResponse("/login")
        elif not path.startswith("/_nicegui"):
            role = (app.storage.user.get("role") or "").lower()
            if not role_allows(path, role):
                return RedirectResponse("/home")

        return await call_next(request)


app.add_static_files("/assets", "app/assets")
app.add_middleware(AuthMiddleware)


@contextmanager
def frame(page_title: str, active_route: str):
    """A reusable layout wrapper that injects the sidebar and standardizes the page container."""
    ui.page_title(page_title)
    ui.query("body").classes("bg-white")
    ui.query(".nicegui-content").classes("pb-32")

    create_sidebar(active_route=active_route)

    def check_session():
        if is_token_expired(app.storage.user.get("token")):
            app.storage.user["authenticated"] = False
            app.storage.user["token"] = None
            ui.notify("Your session has expired. Please log in again.", type="warning")
            ui.navigate.to("/login")

    ui.timer(10.0, check_session)

    with ui.column().classes("w-full max-w-7xl mx-auto overflow-y-auto"):
        yield


@ui.page("/login")
def auth_route():
    login_page()


@ui.page("/home")
@ui.page("/home/quote_create")
@ui.page("/home/quote_edit/{id}")
def home_route():
    with frame(page_title="Home", active_route="/home"):
        home_page()


@ui.page("/agenda")
async def agenda_route():
    with frame(page_title="Agenda", active_route="/agenda"):
        await agenda_page()


@ui.page("/persons")
async def persons_route():
    with frame(page_title="Persons", active_route="/persons"):
        await persons_page()


@ui.page("/pricing")
async def pricing_route():
    with frame(page_title="Pricing", active_route="/pricing"):
        await pricing_page()


@ui.page("/preset")
@ui.page("/preset/create")
@ui.page("/preset/edit/{id}")
def quote_route():
    with frame(page_title="Quotes", active_route="/preset"):
        preset_page()


@ui.page("/settings")
def settings_route():
    with frame(page_title="Settings", active_route="/settings"):
        settings_page()


storage_secret = os.environ.get("NICEGUI_STORAGE_SECRET", "")
if len(storage_secret) < 32:
    raise SystemExit("NICEGUI_STORAGE_SECRET must be set (>= 32 chars). Run scripts/gen-env.sh.")

ui.run(
    title="Syntria",
    storage_secret=storage_secret,
    port=int(os.getenv("NICEGUI_PORT", 8080)),
    host="0.0.0.0",
    reload=os.getenv("NICEGUI_RELOAD", "false").lower() == "true",
    show=False,
    favicon="app/assets/icons/syntria_logo.svg",
    session_middleware_kwargs={
        "https_only": os.getenv("NICEGUI_HTTPS_ONLY", "false").lower() == "true",
        "same_site": "lax",
    },
)
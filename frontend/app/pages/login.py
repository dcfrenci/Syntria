import base64
import json
import time
from collections import defaultdict, deque

from nicegui import app, ui

from api_client.auth import authenticate

# Per-IP limiter (module-level ON PURPOSE: it must be shared by all sessions).
_ip_fails: dict[str, deque[float]] = defaultdict(deque)
IP_MAX_FAILS, IP_WINDOW = 10, 15 * 60


def _client_ip() -> str:
    try:
        req = ui.context.client.request
        # nginx sets X-Real-IP from the trusted real_ip chain; X-Forwarded-For's first hop is client-controlled.
        return req.headers.get("x-real-ip") or (
            req.client.host if req.client else "unknown"
        )
    except Exception:
        return "unknown"


def _ip_blocked(ip: str) -> bool:
    if len(_ip_fails) > 5000:
        cutoff = time.monotonic() - IP_WINDOW
        for k in [k for k, v in _ip_fails.items() if not v or v[-1] < cutoff]:
            _ip_fails.pop(k, None)
    q, now = _ip_fails[ip], time.monotonic()
    while q and now - q[0] > IP_WINDOW:
        q.popleft()
    if not q:
        _ip_fails.pop(ip, None)
    return len(q) >= IP_MAX_FAILS


def login_page():
    if app.storage.user.get("authenticated", False):
        ui.navigate.to("/home")
        return

    with ui.card().classes("absolute-center w-80"):
        ui.image("app/assets/images/syntria.svg")
        ui.space()
        ui.label("Login").classes("w-full text-center text-xl font-bold mb-4")
        username_input = ui.input("Username").classes("w-full")
        password_input = ui.input(
            "Password", password=True, password_toggle_button=True
        ).classes("w-full")

        async def try_login():
            ip = _client_ip()
            if _ip_blocked(ip):
                ui.notify(
                    "Too many failed attempts. Try again in a few minutes.",
                    color="negative",
                )
                return

            result = await authenticate(username_input.value, password_input.value, ip)

            if result and result.get("error"):
                msg = (
                    "Too many failed attempts. Try again in a few minutes."
                    if result["error"] == "rate_limited"
                    else "Service temporarily unavailable."
                )
                ui.notify(msg, color="negative")
                return

            if not result:
                _ip_fails[ip].append(time.monotonic())
                ui.notify("Invalid username or password", color="negative")
                return

            _ip_fails.pop(ip, None)
            app.storage.user["authenticated"] = True
            token = result.get("access_token")
            app.storage.user["token"] = token
            try:
                payload_part = token.split(".")[1]
                padded = payload_part + "=" * (-len(payload_part) % 4)
                payload = json.loads(base64.urlsafe_b64decode(padded))
                app.storage.user["name"] = (
                    f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip()
                )
                app.storage.user["role"] = payload.get("role", "Unknown").capitalize()
            except Exception:
                app.storage.user["name"] = "User"
                app.storage.user["role"] = "Role"
            ui.navigate.to("/home")

        ui.button("Sign In", on_click=try_login).classes("w-full mt-4")

"""CEO dashboard session authentication."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from src.config import settings

CEO_SESSION_COOKIE = "ceo_session"
SESSION_MAX_AGE = 7 * 24 * 3600

PUBLIC_EXACT = {"/login", "/client", "/favicon.ico"}
PUBLIC_PREFIXES = (
    "/static/",
    "/api/auth/login",
    "/api/auth/info",
    "/api/company",
    "/api/client-inquiry",
    "/api/walkgether",
    "/walkgether/",
    "/deliverables/",
    "/preview/",
)


def _make_digest(payload: str) -> str:
    return hmac.new(
        settings.auth_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def _sign(payload: str) -> str:
    return f"{payload}.{_make_digest(payload)}"


def create_session_token(email: str) -> str:
    data = {
        "email": email.strip().lower(),
        "exp": int(time.time()) + SESSION_MAX_AGE,
    }
    payload = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
    return _sign(payload)


def _verify_token(token: str) -> Optional[str]:
    if not token or "." not in token:
        return None
    payload, digest = token.rsplit(".", 1)
    if not hmac.compare_digest(_make_digest(payload), digest):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode()))
    except (json.JSONDecodeError, ValueError):
        return None
    if data.get("exp", 0) < int(time.time()):
        return None
    email = data.get("email", "")
    if email != settings.ceo_login_email.strip().lower():
        return None
    return email


def get_session_email(request: Request) -> Optional[str]:
    token = request.cookies.get(CEO_SESSION_COOKIE)
    if not token:
        return None
    return _verify_token(token)


def is_authenticated(request: Request) -> bool:
    return get_session_email(request) is not None


def credentials_valid(email: str, password: str) -> bool:
    return (
        email.strip().lower() == settings.ceo_login_email.strip().lower()
        and password == settings.ceo_login_password
    )


def is_public_path(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def set_session_cookie(response: Response, email: str) -> None:
    response.set_cookie(
        CEO_SESSION_COOKIE,
        create_session_token(email),
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(CEO_SESSION_COOKIE, path="/")


async def ceo_auth_middleware(request: Request, call_next):
    path = request.url.path

    if is_public_path(path):
        return await call_next(request)

    if path == "/" and not is_authenticated(request):
        return RedirectResponse("/login", status_code=302)

    if path.startswith("/api/") and not is_authenticated(request):
        return JSONResponse(status_code=401, content={"detail": "CEO login required"})

    if path == "/login" and is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    return await call_next(request)

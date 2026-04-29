"""Shared headers for outbound Attendance HTTP calls."""

from collections.abc import AsyncGenerator
from contextvars import ContextVar, Token
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

# Set per HTTP request when the client sends Authorization (e.g. Swagger Authorize).
_upstream_request_token: ContextVar[str | None] = ContextVar("_upstream_request_token", default=None)

_optional_http_bearer = HTTPBearer(auto_error=False)


async def bind_optional_upstream_bearer(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_optional_http_bearer)],
) -> AsyncGenerator[None, None]:
    """Optional Bearer: not required; if present, forwarded to Attendance instead of env token."""
    token = creds.credentials.strip() if creds and creds.credentials else None
    reset: Token = _upstream_request_token.set(token)
    try:
        yield
    finally:
        _upstream_request_token.reset(reset)


def attendance_auth_headers() -> dict[str, str]:
    """Bearer for Attendance: per-request token (Swagger / clients) else ``ATTENDANCE_ACCESS_TOKEN``."""
    req = _upstream_request_token.get()
    t = (req or settings.attendance_access_token or "").strip()
    if not t:
        return {}
    if t.lower().startswith("bearer "):
        return {"Authorization": t}
    return {"Authorization": f"Bearer {t}"}

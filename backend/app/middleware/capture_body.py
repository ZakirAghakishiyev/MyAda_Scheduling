"""Capture raw request body so exception handlers can log it after parse/validation failures."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CaptureRequestBodyMiddleware(BaseHTTPMiddleware):
    """Stores ``request.state.raw_body`` and replays the body for downstream handlers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            body = await request.body()
            request.state.raw_body = body

            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            request._receive = receive  # noqa: SLF001

        return await call_next(request)

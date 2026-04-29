"""Log HTTP / validation failures with request body and error detail (not only access-log lines)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

log = logging.getLogger("app.http")


def _body_preview(request: Request, max_len: int = 16384) -> str | None:
    raw = getattr(request.state, "raw_body", None)
    if not raw:
        return None
    try:
        s = raw.decode("utf-8", errors="replace")
    except Exception:
        return repr(raw[:max_len])
    if len(s) > max_len:
        return s[:max_len] + f"... (truncated, total {len(s)} chars)"
    return s


def _client_host(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


async def logged_request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    body_str = _body_preview(request)
    body_from_exc = getattr(exc, "body", None)
    if body_from_exc is not None and not body_str:
        if isinstance(body_from_exc, (bytes, bytearray)):
            body_str = body_from_exc.decode("utf-8", errors="replace")[:16384]
        else:
            body_str = str(body_from_exc)[:16384]

    log.warning(
        "422 Unprocessable Entity (request validation) | %s %s | client=%s | errors=%s | body=%s",
        request.method,
        request.url.path,
        _client_host(request),
        jsonable_encoder(exc.errors()),
        body_str,
    )
    return await request_validation_exception_handler(request, exc)


async def logged_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> Any:
    body_str = _body_preview(request)
    detail = exc.detail
    if exc.status_code >= 500:
        log.error(
            "HTTP %s | %s %s | client=%s | detail=%s | body=%s",
            exc.status_code,
            request.method,
            request.url.path,
            _client_host(request),
            detail,
            body_str,
        )
    else:
        log.warning(
            "HTTP %s | %s %s | client=%s | detail=%s | body=%s",
            exc.status_code,
            request.method,
            request.url.path,
            _client_host(request),
            detail,
            body_str,
        )
    return await http_exception_handler(request, exc)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
        raise exc
    body_str = _body_preview(request)
    log.exception(
        "Unhandled exception | %s %s | client=%s | body=%s",
        request.method,
        request.url.path,
        _client_host(request),
        body_str,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


async def db_operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    body_str = _body_preview(request)
    log.error(
        "Database operational error | %s %s | client=%s | error=%s | body=%s",
        request.method,
        request.url.path,
        _client_host(request),
        str(exc).splitlines()[0],
        body_str,
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Database unavailable. Check DATABASE_URL and ensure PostgreSQL is running "
                "with valid credentials."
            )
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, logged_request_validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, logged_http_exception_handler)
    app.add_exception_handler(OperationalError, db_operational_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

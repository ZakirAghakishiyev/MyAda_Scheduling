import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routers import preferences, schedules
from app.core.config import cors_middleware_kwargs
from app.core.http_error_handlers import register_exception_handlers
from app.core.logging_config import setup_logging
from app.middleware.capture_body import CaptureRequestBodyMiddleware

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Scheduling microservice",
    version="1.0.0",
    description=(
        "University scheduling: generation, manual edits, instructor preferences.\n\n"
        "**Optional Bearer (Swagger *Authorize*):** if you send `Authorization: Bearer <JWT>`, "
        "that token is used for outbound **Attendance** calls on this request. "
        "Otherwise the server uses `ATTENDANCE_ACCESS_TOKEN` from the environment. "
        "Scheduling routes themselves do not require authentication."
    ),
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    **cors_middleware_kwargs(),
    allow_methods=["*"],
    allow_headers=["*"],
)
# Outermost: capture body first so validation / HTTP error handlers can log it
app.add_middleware(CaptureRequestBodyMiddleware)

app.include_router(schedules.router, prefix="/api/v1")
app.include_router(preferences.router, prefix="/api/v1")

logger.info("Scheduling microservice application loaded")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=307)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

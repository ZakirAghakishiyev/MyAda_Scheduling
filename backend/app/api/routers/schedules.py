from fastapi import APIRouter, Depends, Query

from app.api.deps import DbDep, UserIdDep
from app.clients.attendance_headers import bind_optional_upstream_bearer
from app.core.errors import (
    ConflictError,
    NotFoundError,
    UpstreamError,
    ValidationAppError,
    http_conflict,
    http_not_found,
    http_validation,
)
from app.schemas.schedule import (
    PublishRequest,
    PublishResponse,
    ScheduleGenerateRequest,
    ScheduleGenerateResponse,
    ScheduleRunDetailResponse,
    SessionOptionsResponse,
    SessionOut,
    SessionPatchRequest,
    SessionPatchResponse,
    UnscheduledOut,
)
from app.services import manual as manual_service
from app.services import schedule_generate
from app.services import schedule_publish
from app.services import schedule_query

router = APIRouter(
    prefix="/schedules",
    tags=["schedules"],
    dependencies=[Depends(bind_optional_upstream_bearer)],
)


@router.post("/generate", response_model=ScheduleGenerateResponse)
def post_generate(body: ScheduleGenerateRequest, db: DbDep) -> ScheduleGenerateResponse:
    try:
        return schedule_generate.generate_schedule(db, body.academic_year, body.semester)
    except UpstreamError as e:
        raise http_validation(ValidationAppError(e.message)) from e


@router.get("/{schedule_run_id}", response_model=ScheduleRunDetailResponse)
def get_schedule_run(schedule_run_id: int, db: DbDep) -> ScheduleRunDetailResponse:
    try:
        return schedule_query.get_run_detail(db, schedule_run_id)
    except NotFoundError as e:
        raise http_not_found(e) from e


@router.get("/{schedule_run_id}/sessions", response_model=list[SessionOut])
def get_sessions(
    schedule_run_id: int,
    db: DbDep,
    day: str | None = Query(None),
    instructor_user_id: str | None = Query(None),
) -> list[SessionOut]:
    try:
        return schedule_query.list_sessions(db, schedule_run_id, day, instructor_user_id)
    except NotFoundError as e:
        raise http_not_found(e) from e
    except ValidationAppError as e:
        raise http_validation(e) from e


@router.get("/{schedule_run_id}/unscheduled", response_model=list[UnscheduledOut])
def get_unscheduled(schedule_run_id: int, db: DbDep) -> list[UnscheduledOut]:
    try:
        return schedule_query.list_unscheduled(db, schedule_run_id)
    except NotFoundError as e:
        raise http_not_found(e) from e


@router.patch(
    "/{schedule_run_id}/sessions/{session_id}",
    response_model=SessionPatchResponse,
)
def patch_session(
    schedule_run_id: int,
    session_id: int,
    body: SessionPatchRequest,
    db: DbDep,
    user_id: UserIdDep,
) -> SessionPatchResponse:
    try:
        session = manual_service.patch_session(db, schedule_run_id, session_id, body, user_id)
        return SessionPatchResponse(session=session)
    except NotFoundError as e:
        raise http_not_found(e) from e
    except ConflictError as e:
        raise http_conflict(e) from e
    except ValidationAppError as e:
        raise http_validation(e) from e


@router.get(
    "/{schedule_run_id}/sessions/{session_id}/options",
    response_model=SessionOptionsResponse,
)
def get_session_options(
    schedule_run_id: int,
    session_id: int,
    db: DbDep,
) -> SessionOptionsResponse:
    try:
        return manual_service.session_options(db, schedule_run_id, session_id)
    except NotFoundError as e:
        raise http_not_found(e) from e
    except ValidationAppError as e:
        raise http_validation(e) from e


@router.post("/{schedule_run_id}/publish", response_model=PublishResponse)
def post_publish(
    schedule_run_id: int,
    body: PublishRequest,
    db: DbDep,
    user_id: UserIdDep,
) -> PublishResponse:
    try:
        return schedule_publish.publish_schedule(db, schedule_run_id, user_id, body)
    except NotFoundError as e:
        raise http_not_found(e) from e
    except UpstreamError as e:
        raise http_validation(ValidationAppError(e.message)) from e
    except ValidationAppError as e:
        raise http_validation(e) from e

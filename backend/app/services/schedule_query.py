from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.location import fetch_rooms
from app.core.errors import NotFoundError, ValidationAppError
from app.core.user_ids import normalize_instructor_user_id
from app.db.models import ScheduleRun, ScheduledSession, UnscheduledLesson
from app.schemas.schedule import ScheduleRunDetailResponse, SessionOut, UnscheduledOut
from app.services.room_labels import enrich_sessions_to_out, enrich_unscheduled_rows


def get_run_or_404(db: Session, schedule_run_id: int) -> ScheduleRun:
    run = db.execute(select(ScheduleRun).where(ScheduleRun.id == schedule_run_id)).scalar_one_or_none()
    if not run:
        raise NotFoundError("Schedule run not found")
    return run


def get_run_detail(db: Session, schedule_run_id: int) -> ScheduleRunDetailResponse:
    run = get_run_or_404(db, schedule_run_id)
    return ScheduleRunDetailResponse.model_validate(run)


def list_sessions(
    db: Session, schedule_run_id: int, day: str | None, instructor_user_id: str | None
) -> list[SessionOut]:
    get_run_or_404(db, schedule_run_id)
    q = select(ScheduledSession).where(ScheduledSession.schedule_run_id == schedule_run_id)
    if day:
        q = q.where(ScheduledSession.day == day)
    if instructor_user_id is not None and instructor_user_id.strip() != "":
        try:
            iid = normalize_instructor_user_id(instructor_user_id)
        except ValueError as e:
            raise ValidationAppError(str(e)) from e
        q = q.where(ScheduledSession.instructor_user_id == iid)
    q = q.order_by(ScheduledSession.day, ScheduledSession.start_time, ScheduledSession.id)
    rows = db.execute(q).scalars().all()
    return enrich_sessions_to_out(rows, fetch_rooms())


def list_unscheduled(db: Session, schedule_run_id: int) -> list[UnscheduledOut]:
    get_run_or_404(db, schedule_run_id)
    rows = db.execute(
        select(UnscheduledLesson)
        .where(UnscheduledLesson.schedule_run_id == schedule_run_id)
        .order_by(UnscheduledLesson.id)
    ).scalars().all()
    return enrich_unscheduled_rows(rows, fetch_rooms())

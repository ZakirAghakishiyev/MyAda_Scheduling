from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.models import ScheduleRun, ScheduledSession, UnscheduledLesson
from app.schemas.schedule import ScheduleRunDetailResponse, SessionOut, UnscheduledOut


def get_run_or_404(db: Session, schedule_run_id: int) -> ScheduleRun:
    run = db.execute(select(ScheduleRun).where(ScheduleRun.id == schedule_run_id)).scalar_one_or_none()
    if not run:
        raise NotFoundError("Schedule run not found")
    return run


def get_run_detail(db: Session, schedule_run_id: int) -> ScheduleRunDetailResponse:
    run = get_run_or_404(db, schedule_run_id)
    return ScheduleRunDetailResponse.model_validate(run)


def list_sessions(
    db: Session, schedule_run_id: int, day: str | None, instructor_user_id: int | None
) -> list[SessionOut]:
    get_run_or_404(db, schedule_run_id)
    q = select(ScheduledSession).where(ScheduledSession.schedule_run_id == schedule_run_id)
    if day:
        q = q.where(ScheduledSession.day == day)
    if instructor_user_id is not None:
        q = q.where(ScheduledSession.instructor_user_id == instructor_user_id)
    q = q.order_by(ScheduledSession.day, ScheduledSession.start_time, ScheduledSession.id)
    rows = db.execute(q).scalars().all()
    return [SessionOut.model_validate(r) for r in rows]


def list_unscheduled(db: Session, schedule_run_id: int) -> list[UnscheduledOut]:
    get_run_or_404(db, schedule_run_id)
    rows = db.execute(
        select(UnscheduledLesson)
        .where(UnscheduledLesson.schedule_run_id == schedule_run_id)
        .order_by(UnscheduledLesson.id)
    ).scalars().all()
    return [UnscheduledOut.model_validate(r) for r in rows]

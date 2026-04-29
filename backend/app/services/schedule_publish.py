from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.attendance_sessions import WeeklySessionSlotPayload, bulk_generate_lesson_sessions
from app.core.errors import ValidationAppError
from app.db.models import ScheduleRunStatus, ScheduledSession
from app.schemas.schedule import (
    AttendanceLessonGenerationOut,
    PublishRequest,
    PublishResponse,
)
from app.services import audit as audit_service
from app.services.schedule_query import get_run_or_404
from app.scheduler.timeslots import DAY_ORDER

_MAX_PUBLISH_SPAN_DAYS = 731


def _normalize_time_hhmmss(t: str) -> str:
    t = (t or "").strip()
    parts = t.split(":")
    if len(parts) == 2:
        return f"{parts[0]}:{parts[1]}:00"
    if len(parts) >= 3:
        return f"{parts[0]}:{parts[1]}:{parts[2][:2]}"
    return t


def _weekly_slots_for_lesson(rows: list[ScheduledSession]) -> list[WeeklySessionSlotPayload]:
    seen: set[tuple[str, str, str]] = set()
    slots: list[WeeklySessionSlotPayload] = []
    for r in rows:
        key = (r.day, r.start_time, r.end_time)
        if key in seen:
            continue
        seen.add(key)
        slots.append(
            WeeklySessionSlotPayload(
                day_of_week=r.day,
                start_time=_normalize_time_hhmmss(r.start_time),
                end_time=_normalize_time_hhmmss(r.end_time),
            )
        )

    def sort_key(s: WeeklySessionSlotPayload) -> tuple[int, str]:
        day_idx = DAY_ORDER.index(s.day_of_week) if s.day_of_week in DAY_ORDER else 99
        return (day_idx, s.start_time)

    slots.sort(key=sort_key)
    return slots


def publish_schedule(
    db: Session,
    schedule_run_id: int,
    actor_user_id: str,
    body: PublishRequest,
) -> PublishResponse:
    run = get_run_or_404(db, schedule_run_id)
    if run.status != ScheduleRunStatus.completed.value:
        raise ValidationAppError("Only a completed schedule run can be published")

    if body.from_date > body.to_date:
        raise ValidationAppError("from_date must be on or before to_date")
    span = (body.to_date - body.from_date).days + 1
    if span > _MAX_PUBLISH_SPAN_DAYS:
        raise ValidationAppError(f"Date span must be at most {_MAX_PUBLISH_SPAN_DAYS} days")

    session_rows = db.execute(
        select(ScheduledSession).where(ScheduledSession.schedule_run_id == schedule_run_id)
    ).scalars().all()

    if not session_rows:
        raise ValidationAppError("No scheduled sessions to publish")

    by_lesson: dict[int, list[ScheduledSession]] = {}
    for row in session_rows:
        by_lesson.setdefault(row.lesson_id, []).append(row)

    generations: list[AttendanceLessonGenerationOut] = []
    lesson_ids = sorted(by_lesson.keys())
    for lesson_id in lesson_ids:
        weekly = _weekly_slots_for_lesson(by_lesson[lesson_id])
        if not weekly:
            raise ValidationAppError(f"No weekly slots derived for lesson {lesson_id}")
        res = bulk_generate_lesson_sessions(
            lesson_id,
            body.from_date,
            body.to_date,
            weekly,
            topic=body.topic,
        )
        generations.append(
            AttendanceLessonGenerationOut(
                lesson_id=lesson_id,
                created_count=res.created_count,
                skipped_duplicate_count=res.skipped_duplicate_count,
            )
        )

    prev = run.status
    run.status = ScheduleRunStatus.published.value
    audit_service.log_change(
        db,
        schedule_run_id=schedule_run_id,
        session_id=None,
        actor_user_id=actor_user_id,
        action="publish",
        before_state={"status": prev},
        after_state={
            "status": run.status,
            "from_date": body.from_date.isoformat(),
            "to_date": body.to_date.isoformat(),
            "attendance_generations": [g.model_dump() for g in generations],
        },
    )
    db.commit()
    db.refresh(run)
    return PublishResponse(
        schedule_run_id=run.id,
        status=run.status,
        attendance_generations=generations,
    )

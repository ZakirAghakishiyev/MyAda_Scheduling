from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.attendance import fetch_lessons_for_scheduling
from app.clients.location import fetch_rooms
from app.core.errors import UpstreamError
from app.db.models import ScheduleRun, ScheduleRunStatus, ScheduledSession, UnscheduledLesson
from app.scheduler.engine import LessonInput, RoomInput, build_summary, run_scheduler
from app.scheduler.timeslots import DAY_ORDER, TIMESLOTS
from app.schemas.schedule import (
    ScheduleGenerateResponse,
    ScheduleSummary,
    SessionOut,
    UnscheduledOut,
)
from app.services import preferences as pref_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_schedule(db: Session, academic_year: str, semester: str) -> ScheduleGenerateResponse:
    run = ScheduleRun(
        academic_year=academic_year,
        semester=semester,
        status=ScheduleRunStatus.running.value,
        started_at=_utcnow(),
    )
    db.add(run)
    db.flush()

    try:
        lesson_dtos = fetch_lessons_for_scheduling()
        room_dtos = fetch_rooms()
    except Exception as e:
        run.status = ScheduleRunStatus.failed.value
        run.completed_at = _utcnow()
        run.error_message = str(e)
        db.commit()
        raise

    if not room_dtos:
        run.status = ScheduleRunStatus.failed.value
        run.completed_at = _utcnow()
        run.error_message = "No rooms returned from Location service"
        db.commit()
        raise UpstreamError(run.error_message)

    instructor_ids = {l.instructor_user_id for l in lesson_dtos}
    pref_inputs = pref_service.load_engine_preferences(db, instructor_ids, academic_year, semester)

    lessons: list[LessonInput] = []
    for l in lesson_dtos:
        lessons.append(
            {
                "lesson_id": l.lesson_id,
                "instructor_user_id": l.instructor_user_id,
                "course_code": l.course_code,
                "course_title": l.course_title,
                "times_per_week": l.times_per_week,
                "enrollment": l.enrollment,
                "max_capacity": l.max_capacity,
            }
        )

    rooms: list[RoomInput] = [{"id": r.id, "name": r.name, "capacity": r.capacity} for r in room_dtos]

    scheduled, unscheduled = run_scheduler(lessons, rooms, TIMESLOTS, pref_inputs, DAY_ORDER)
    summary_dict: dict = build_summary(scheduled, unscheduled)

    for block in scheduled:
        seq = 0
        for sess in block.get("sessions", []):
            db.add(
                ScheduledSession(
                    schedule_run_id=run.id,
                    lesson_id=int(block["lesson_id"]),
                    instructor_user_id=int(block["instructor_user_id"]),
                    room_id=int(sess["room_id"]),
                    room_name=str(sess["room_name"]),
                    timeslot_id=str(sess["slot_id"]),
                    day=str(sess["day"]),
                    start_time=str(sess["start"]),
                    end_time=str(sess["end"]),
                    preference_match=bool(sess.get("preference_match")),
                    sequence_index=seq,
                    course_code=block.get("course_code"),
                    course_title=block.get("course_title"),
                    enrollment=int(block.get("enrollment", 0)),
                    room_capacity=int(sess.get("room_capacity", 0)),
                )
            )
            seq += 1

    for block in unscheduled:
        db.add(
            UnscheduledLesson(
                schedule_run_id=run.id,
                lesson_id=int(block["lesson_id"]),
                instructor_user_id=int(block["instructor_user_id"]),
                times_per_week=int(block["times_per_week"]),
                sessions_assigned=int(block["sessions_assigned"]),
                sessions_needed=int(block["sessions_needed"]),
                reason=str(block["reason"]),
                partial_sessions=block.get("partial_sessions"),
                course_code=block.get("course_code"),
                course_title=block.get("course_title"),
                enrollment=int(block.get("enrollment", 0)),
            )
        )

    run.status = ScheduleRunStatus.completed.value
    run.completed_at = _utcnow()
    run.summary = summary_dict
    db.commit()
    db.refresh(run)

    sessions = db.execute(
        select(ScheduledSession)
        .where(ScheduledSession.schedule_run_id == run.id)
        .order_by(ScheduledSession.id)
    ).scalars().all()
    uns = db.execute(
        select(UnscheduledLesson)
        .where(UnscheduledLesson.schedule_run_id == run.id)
        .order_by(UnscheduledLesson.id)
    ).scalars().all()

    summ = ScheduleSummary(
        total_lessons=summary_dict["total_lessons"],
        scheduled_lesson_count=summary_dict["scheduled_lesson_count"],
        unscheduled_lesson_count=summary_dict["unscheduled_lesson_count"],
        scheduled_session_count=summary_dict["scheduled_session_count"],
        preference_match_sessions=summary_dict["preference_match_sessions"],
    )

    return ScheduleGenerateResponse(
        schedule_run_id=run.id,
        status=run.status,
        academic_year=run.academic_year,
        semester=run.semester,
        summary=summ,
        scheduled_sessions=[SessionOut.model_validate(s) for s in sessions],
        unscheduled_lessons=[UnscheduledOut.model_validate(u) for u in uns],
    )

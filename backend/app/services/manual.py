from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.location import RoomDto, fetch_rooms
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.db.models import ScheduledSession, ScheduleRunStatus
from app.scheduler.timeslots import TIMESLOT_BY_ID
from app.schemas.schedule import SessionOptionsResponse, SessionOut, SessionPatchRequest
from app.services import audit as audit_service
from app.services.schedule_query import get_run_or_404


def _rooms_by_id(rooms: list[RoomDto]) -> dict[int, RoomDto]:
    return {r.id: r for r in rooms}


def _session_snapshot(s: ScheduledSession) -> dict:
    return {
        "room_id": s.room_id,
        "room_name": s.room_name,
        "timeslot_id": s.timeslot_id,
        "day": s.day,
        "start_time": s.start_time,
        "end_time": s.end_time,
    }


def patch_session(
    db: Session,
    schedule_run_id: int,
    session_id: int,
    body: SessionPatchRequest,
    actor_user_id: int,
) -> SessionOut:
    run = get_run_or_404(db, schedule_run_id)
    if run.status not in (ScheduleRunStatus.completed.value, ScheduleRunStatus.published.value):
        raise ValidationAppError("Schedule run must be completed or published to edit sessions")

    if body.room_id is None and body.timeslot_id is None:
        raise ValidationAppError("Provide room_id and/or timeslot_id")

    sess = db.execute(
        select(ScheduledSession).where(
            ScheduledSession.id == session_id,
            ScheduledSession.schedule_run_id == schedule_run_id,
        )
    ).scalar_one_or_none()
    if not sess:
        raise NotFoundError("Session not found")

    rooms = fetch_rooms()
    rmap = _rooms_by_id(rooms)

    new_room_id = body.room_id if body.room_id is not None else sess.room_id
    new_timeslot_id = body.timeslot_id if body.timeslot_id is not None else sess.timeslot_id

    if new_room_id not in rmap:
        raise ValidationAppError(f"Unknown room_id: {new_room_id}")
    slot = TIMESLOT_BY_ID.get(new_timeslot_id)
    if not slot:
        raise ValidationAppError(f"Unknown timeslot_id: {new_timeslot_id}")

    room = rmap[new_room_id]
    need = sess.enrollment if sess.enrollment > 0 else 0
    if need > 0 and room.capacity < need:
        raise ConflictError(
            f"Room capacity {room.capacity} is below required enrollment ({need})"
        )

    others = db.execute(
        select(ScheduledSession).where(
            ScheduledSession.schedule_run_id == schedule_run_id,
            ScheduledSession.id != session_id,
        )
    ).scalars().all()

    for o in others:
        if o.instructor_user_id == sess.instructor_user_id and o.timeslot_id == new_timeslot_id:
            raise ConflictError("Instructor already has another session in this timeslot")
        if o.room_id == new_room_id and o.timeslot_id == new_timeslot_id:
            raise ConflictError("Room is already booked for this timeslot")

    before = _session_snapshot(sess)

    sess.room_id = new_room_id
    sess.room_name = room.name
    sess.timeslot_id = new_timeslot_id
    sess.day = slot["day"]
    sess.start_time = slot["start"]
    sess.end_time = slot["end"]
    sess.room_capacity = room.capacity

    after = _session_snapshot(sess)

    audit_service.log_change(
        db,
        schedule_run_id=schedule_run_id,
        session_id=session_id,
        actor_user_id=actor_user_id,
        action="manual_patch",
        before_state=before,
        after_state=after,
    )
    db.commit()
    db.refresh(sess)
    return SessionOut.model_validate(sess)


def session_options(
    db: Session, schedule_run_id: int, session_id: int
) -> SessionOptionsResponse:
    run = get_run_or_404(db, schedule_run_id)
    if run.status not in (ScheduleRunStatus.completed.value, ScheduleRunStatus.published.value):
        raise ValidationAppError("Schedule run must be completed or published")

    sess = db.execute(
        select(ScheduledSession).where(
            ScheduledSession.id == session_id,
            ScheduledSession.schedule_run_id == schedule_run_id,
        )
    ).scalar_one_or_none()
    if not sess:
        raise NotFoundError("Session not found")

    rooms = fetch_rooms()
    others = db.execute(
        select(ScheduledSession).where(
            ScheduledSession.schedule_run_id == schedule_run_id,
            ScheduledSession.id != session_id,
        )
    ).scalars().all()
    blocked_inst_slots = {(o.instructor_user_id, o.timeslot_id) for o in others}
    blocked_room_slots = {(o.room_id, o.timeslot_id) for o in others}

    need = sess.enrollment if sess.enrollment > 0 else 0
    options: list[dict] = []
    for ts_id, slot in TIMESLOT_BY_ID.items():
        for room in sorted(rooms, key=lambda r: r.capacity):
            if need > 0 and room.capacity < need:
                continue
            if (sess.instructor_user_id, ts_id) in blocked_inst_slots:
                continue
            if (room.id, ts_id) in blocked_room_slots:
                continue
            options.append(
                {
                    "room_id": room.id,
                    "room_name": room.name,
                    "timeslot_id": ts_id,
                    "day": slot["day"],
                    "start": slot["start"],
                    "end": slot["end"],
                }
            )

    return SessionOptionsResponse(options=options)

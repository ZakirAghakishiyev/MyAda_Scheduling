"""Human-readable room labels from Location `RoomDto` (building + room number)."""

from __future__ import annotations

from typing import Any

from app.clients.location import RoomDto
from app.db.models import ScheduledSession, UnscheduledLesson
from app.schemas.schedule import SessionOut, UnscheduledOut


def format_room_display(room: RoomDto) -> str:
    """
    Prefer *single-letter* last word of building name + room number (e.g. ``Building A`` + ``101`` → ``A101``).
    Otherwise concatenate compact building words + number (e.g. ``MainHall101``).
    Falls back to room ``name`` when number is missing.
    """
    b = (room.building_name or "").strip()
    n = (room.number or "").strip()
    if not n:
        return (room.name or "").strip()
    if not b:
        return n
    parts = b.split()
    if parts and len(parts[-1]) == 1 and parts[-1].isalpha():
        return f"{parts[-1]}{n}"
    return f"{''.join(parts)}{n}"


def enrich_sessions_to_out(rows: list[ScheduledSession], rooms: list[RoomDto]) -> list[SessionOut]:
    """Replace ``room_name`` on each ``SessionOut`` using current Location data for ``room_id``."""
    by_id = {r.id: r for r in rooms}
    out: list[SessionOut] = []
    for s in rows:
        base = SessionOut.model_validate(s)
        r = by_id.get(s.room_id)
        if r is not None:
            base = base.model_copy(update={"room_name": format_room_display(r)})
        out.append(base)
    return out


def label_partial_session_dicts(
    items: list[Any] | None, room_by_id: dict[int, RoomDto]
) -> list[Any] | None:
    """Set ``room_name`` on scheduler partial session dicts (``room_id`` + Location row)."""
    if items is None:
        return None
    out: list[Any] = []
    for item in items:
        if not isinstance(item, dict):
            out.append(item)
            continue
        d = dict(item)
        rid = d.get("room_id")
        if isinstance(rid, int) and rid in room_by_id:
            d["room_name"] = format_room_display(room_by_id[rid])
        out.append(d)
    return out


def enrich_unscheduled_rows(rows: list[UnscheduledLesson], rooms: list[RoomDto]) -> list[UnscheduledOut]:
    """Relabel ``partial_sessions[*].room_name`` from Location for GET responses."""
    by_id = {r.id: r for r in rooms}
    out: list[UnscheduledOut] = []
    for u in rows:
        base = UnscheduledOut.model_validate(u)
        ps = u.partial_sessions
        if ps:
            labeled = label_partial_session_dicts(list(ps), by_id)
            base = base.model_copy(update={"partial_sessions": labeled})
        out.append(base)
    return out

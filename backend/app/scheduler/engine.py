"""
Constraint scheduler ported from nodes/constraint_solver_node.py.
Uses instructor_user_id and room_id as stable keys; lessons include lesson_id and course_code.
"""

from __future__ import annotations

from typing import Any, TypedDict


class RoomInput(TypedDict):
    id: int
    name: str
    capacity: int


class LessonInput(TypedDict, total=False):
    lesson_id: int
    instructor_user_id: int
    course_code: str
    course_title: str
    times_per_week: int
    enrollment: int
    max_capacity: int


class PreferenceInput(TypedDict, total=False):
    instructor_user_id: int
    preferred_days: list[str]
    preferred_times: list[str]
    strict: bool


class ScheduledLessonOut(TypedDict, total=False):
    lesson_id: int
    instructor_user_id: int
    course_code: str
    course_title: str
    times_per_week: int
    enrollment: int
    max_capacity: int
    sessions: list[dict[str, Any]]


class UnscheduledLessonOut(TypedDict, total=False):
    lesson_id: int
    instructor_user_id: int
    course_code: str
    course_title: str
    times_per_week: int
    enrollment: int
    max_capacity: int
    sessions_assigned: int
    sessions_needed: int
    reason: str
    partial_sessions: list[dict[str, Any]]


def _time_category(start: str) -> str:
    hour = int(start.split(":")[0])
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def _slot_score(slot: dict[str, str], pref: dict[str, Any]) -> int:
    preferred_days = pref.get("preferred_days", [])
    preferred_times = pref.get("preferred_times", [])
    day_ok = not preferred_days or slot["day"] in preferred_days
    time_ok = not preferred_times or _time_category(slot["start"]) in preferred_times
    if day_ok and time_ok:
        return 0
    if day_ok or time_ok:
        return 1
    return 2


def _build_pref_index(prefs: list[PreferenceInput]) -> dict[int, dict[str, Any]]:
    index: dict[int, dict[str, Any]] = {}
    for pref in prefs:
        uid = int(pref["instructor_user_id"])
        index[uid] = {
            "preferred_days": [d.capitalize() for d in pref.get("preferred_days", [])],
            "preferred_times": pref.get("preferred_times", []),
            "strict": pref.get("strict", False),
        }
    return index


def run_scheduler(
    lessons: list[LessonInput],
    rooms: list[RoomInput],
    timeslots: list[dict[str, str]],
    instructor_preferences: list[PreferenceInput],
    day_order: list[str],
) -> tuple[list[ScheduledLessonOut], list[UnscheduledLessonOut]]:
    pref_index = _build_pref_index(instructor_preferences)
    room_booked: dict[int, set[str]] = {r["id"]: set() for r in rooms}
    instructor_booked: dict[int, set[str]] = {}
    day_load: dict[str, int] = {d: 0 for d in day_order}
    scheduled: list[ScheduledLessonOut] = []
    unscheduled: list[UnscheduledLessonOut] = []

    for lesson in lessons:
        lesson_id = int(lesson["lesson_id"])
        instructor_user_id = int(lesson["instructor_user_id"])
        course_code = lesson.get("course_code") or "UNKNOWN"
        course_title = lesson.get("course_title") or ""
        times_per_week = int(lesson.get("times_per_week", 1))
        enrollment = int(lesson.get("enrollment", 0))
        max_capacity = int(lesson.get("max_capacity", 0))

        if instructor_user_id not in instructor_booked:
            instructor_booked[instructor_user_id] = set()

        pref = pref_index.get(instructor_user_id, {})
        strict = bool(pref.get("strict", False))
        sessions_assigned: list[dict[str, Any]] = []
        sessions_needed = times_per_week

        for _ in range(sessions_needed):
            assigned = False
            candidate_slots = sorted(
                timeslots,
                key=lambda ts: (_slot_score(ts, pref), day_load[ts["day"]]),
            )
            if strict:
                preferred_days = pref.get("preferred_days", [])
                preferred_times = pref.get("preferred_times", [])
                filtered = [
                    ts
                    for ts in candidate_slots
                    if (not preferred_days or ts["day"] in preferred_days)
                    and (
                        not preferred_times
                        or _time_category(ts["start"]) in preferred_times
                    )
                ]
                candidate_slots = filtered if filtered else candidate_slots

            for slot in candidate_slots:
                slot_id = slot["id"]
                if slot_id in instructor_booked[instructor_user_id]:
                    continue
                room_found: RoomInput | None = None
                for room in sorted(rooms, key=lambda r: r["capacity"]):
                    need = enrollment if enrollment > 0 else max_capacity
                    if need > 0 and room["capacity"] < need:
                        continue
                    if slot_id in room_booked[room["id"]]:
                        continue
                    room_found = room
                    break
                if room_found:
                    instructor_booked[instructor_user_id].add(slot_id)
                    room_booked[room_found["id"]].add(slot_id)
                    day_load[slot["day"]] += 1
                    sessions_assigned.append(
                        {
                            "slot_id": slot_id,
                            "day": slot["day"],
                            "start": slot["start"],
                            "end": slot["end"],
                            "room_id": room_found["id"],
                            "room_name": room_found["name"],
                            "room_capacity": room_found["capacity"],
                            "preference_match": _slot_score(slot, pref) == 0,
                        }
                    )
                    assigned = True
                    break
            if not assigned:
                break

        if len(sessions_assigned) == sessions_needed:
            scheduled.append(
                {
                    "lesson_id": lesson_id,
                    "instructor_user_id": instructor_user_id,
                    "course_code": course_code,
                    "course_title": course_title,
                    "times_per_week": times_per_week,
                    "enrollment": enrollment,
                    "max_capacity": max_capacity,
                    "sessions": sessions_assigned,
                }
            )
        else:
            unscheduled.append(
                {
                    "lesson_id": lesson_id,
                    "instructor_user_id": instructor_user_id,
                    "course_code": course_code,
                    "course_title": course_title,
                    "times_per_week": times_per_week,
                    "enrollment": enrollment,
                    "max_capacity": max_capacity,
                    "sessions_assigned": len(sessions_assigned),
                    "sessions_needed": sessions_needed,
                    "reason": (
                        "No available timeslot/room combination found for all sessions. "
                        f"Assigned {len(sessions_assigned)}/{sessions_needed}."
                    ),
                    "partial_sessions": sessions_assigned,
                }
            )

    return scheduled, unscheduled


def build_summary(
    scheduled: list[ScheduledLessonOut], unscheduled: list[UnscheduledLessonOut]
) -> dict[str, Any]:
    pref_matches = 0
    session_count = 0
    for lesson in scheduled:
        for s in lesson.get("sessions", []):
            session_count += 1
            if s.get("preference_match"):
                pref_matches += 1
    return {
        "total_lessons": len(scheduled) + len(unscheduled),
        "scheduled_lesson_count": len(scheduled),
        "unscheduled_lesson_count": len(unscheduled),
        "scheduled_session_count": session_count,
        "preference_match_sessions": pref_matches,
    }

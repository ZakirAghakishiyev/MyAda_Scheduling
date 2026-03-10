from typing import Any, Dict, List

from vellum.workflows import BaseNode

from ..inputs import Inputs

ROOMS = [
    {"name": "Room 101", "capacity": 30},
    {"name": "Room 102", "capacity": 25},
    {"name": "Room 201", "capacity": 40},
    {"name": "Room 202", "capacity": 20},
    {"name": "Lab A", "capacity": 35},
    {"name": "Lab B", "capacity": 35},
]
TIMESLOTS = [
    {"id": "MON_0800", "day": "Monday", "start": "08:00", "end": "09:30"},
    {"id": "MON_1000", "day": "Monday", "start": "10:00", "end": "11:30"},
    {"id": "MON_1300", "day": "Monday", "start": "13:00", "end": "14:30"},
    {"id": "MON_1500", "day": "Monday", "start": "15:00", "end": "16:30"},
    {"id": "TUE_0800", "day": "Tuesday", "start": "08:00", "end": "09:30"},
    {"id": "TUE_1000", "day": "Tuesday", "start": "10:00", "end": "11:30"},
    {"id": "TUE_1300", "day": "Tuesday", "start": "13:00", "end": "14:30"},
    {"id": "TUE_1500", "day": "Tuesday", "start": "15:00", "end": "16:30"},
    {"id": "WED_0800", "day": "Wednesday", "start": "08:00", "end": "09:30"},
    {"id": "WED_1000", "day": "Wednesday", "start": "10:00", "end": "11:30"},
    {"id": "WED_1300", "day": "Wednesday", "start": "13:00", "end": "14:30"},
    {"id": "WED_1500", "day": "Wednesday", "start": "15:00", "end": "16:30"},
    {"id": "THU_0800", "day": "Thursday", "start": "08:00", "end": "09:30"},
    {"id": "THU_1000", "day": "Thursday", "start": "10:00", "end": "11:30"},
    {"id": "THU_1300", "day": "Thursday", "start": "13:00", "end": "14:30"},
    {"id": "THU_1500", "day": "Thursday", "start": "15:00", "end": "16:30"},
    {"id": "FRI_0800", "day": "Friday", "start": "08:00", "end": "09:30"},
    {"id": "FRI_1000", "day": "Friday", "start": "10:00", "end": "11:30"},
    {"id": "FRI_1300", "day": "Friday", "start": "13:00", "end": "14:30"},
    {"id": "FRI_1500", "day": "Friday", "start": "15:00", "end": "16:30"},
]
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


class ConstraintSolverNode(BaseNode):
    lessons: List[Dict[str, Any]] = Inputs.lessons
    instructor_preferences: List[Dict[str, Any]] = Inputs.instructor_preferences

    class Outputs(BaseNode.Outputs):
        scheduled: list[dict[str, Any]]
        unscheduled: list[dict[str, Any]]

    class Display(BaseNode.Display):
        x = 436
        z_index = 3
        icon = "vellum:icon:calendar"
        color = "teal"

    def _build_pref_index(self) -> Dict[str, Dict]:
        """Build a lookup: instructor -> {preferred_days, preferred_times, strict}"""
        index: Dict[str, Dict] = {}
        for pref in self.instructor_preferences:
            name = pref.get("instructor", "")
            index[name] = {
                "preferred_days": [
                    d.capitalize() for d in pref.get("preferred_days", [])
                ],
                "preferred_times": pref.get("preferred_times", []),
                "strict": pref.get("strict", False),
            }
        return index

    def _time_category(self, start: str) -> str:
        hour = int(start.split(":")[0])
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        return "evening"

    def _slot_score(self, slot: Dict, pref: Dict) -> int:
        """Lower score = more preferred. 0=perfect, 1=day ok/time not, 2=neither preferred."""
        preferred_days = pref.get("preferred_days", [])
        preferred_times = pref.get("preferred_times", [])
        day_ok = not preferred_days or slot["day"] in preferred_days
        time_ok = (
            not preferred_times or self._time_category(slot["start"]) in preferred_times
        )
        if day_ok and time_ok:
            return 0
        if day_ok or time_ok:
            return 1
        return 2

    def run(self) -> BaseNode.Outputs:
        pref_index = self._build_pref_index()
        room_booked: Dict[str, set] = {r["name"]: set() for r in ROOMS}
        instructor_booked: Dict[str, set] = {}
        day_load: Dict[str, int] = {d: 0 for d in DAY_ORDER}
        scheduled = []
        unscheduled = []
        for lesson in self.lessons:
            crn = lesson.get("crn", "UNKNOWN")
            instructor = lesson.get("instructor", "")
            times_per_week = int(lesson.get("times_per_week", 1))
            enrollment = int(lesson.get("enrollment", 0))
            if instructor not in instructor_booked:
                instructor_booked[instructor] = set()
            pref = pref_index.get(instructor, {})
            strict = pref.get("strict", False)
            sessions_assigned = []
            sessions_needed = times_per_week
            for _ in range(sessions_needed):
                assigned = False
                candidate_slots = sorted(
                    TIMESLOTS,
                    key=lambda ts: (self._slot_score(ts, pref), day_load[ts["day"]]),
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
                            or self._time_category(ts["start"]) in preferred_times
                        )
                    ]
                    candidate_slots = filtered if filtered else candidate_slots
                for slot in candidate_slots:
                    slot_id = slot["id"]
                    if slot_id in instructor_booked[instructor]:
                        continue
                    room_found = None
                    for room in sorted(ROOMS, key=lambda r: r["capacity"]):
                        if enrollment > 0 and room["capacity"] < enrollment:
                            continue
                        if slot_id in room_booked[room["name"]]:
                            continue
                        room_found = room
                        break
                    if room_found:
                        instructor_booked[instructor].add(slot_id)
                        room_booked[room_found["name"]].add(slot_id)
                        day_load[slot["day"]] += 1
                        sessions_assigned.append(
                            {
                                "slot_id": slot_id,
                                "day": slot["day"],
                                "start": slot["start"],
                                "end": slot["end"],
                                "room": room_found["name"],
                                "room_capacity": room_found["capacity"],
                                "preference_match": self._slot_score(slot, pref) == 0,
                            }
                        )
                        assigned = True
                        break
                if not assigned:
                    break
            if len(sessions_assigned) == sessions_needed:
                scheduled.append(
                    {
                        "crn": crn,
                        "instructor": instructor,
                        "times_per_week": times_per_week,
                        "enrollment": enrollment,
                        "sessions": sessions_assigned,
                    }
                )
            else:
                unscheduled.append(
                    {
                        "crn": crn,
                        "instructor": instructor,
                        "times_per_week": times_per_week,
                        "enrollment": enrollment,
                        "sessions_assigned": len(sessions_assigned),
                        "sessions_needed": sessions_needed,
                        "reason": f"No available timeslot/room combination found for all sessions. Assigned {len(sessions_assigned)}/{sessions_needed}.",
                        "partial_sessions": sessions_assigned,
                    }
                )
        return self.Outputs(scheduled=scheduled, unscheduled=unscheduled)

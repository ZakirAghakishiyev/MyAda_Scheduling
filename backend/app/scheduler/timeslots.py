"""Canonical timeslot grid (ported from constraint_solver_node prototype)."""

TIMESLOTS: list[dict[str, str]] = [
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

TIMESLOT_BY_ID: dict[str, dict[str, str]] = {t["id"]: t for t in TIMESLOTS}

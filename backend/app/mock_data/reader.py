"""Load mock rooms / lessons / instructors from CSV files shipped under app/mock_data/."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

from app.clients.attendance import SchedulingLessonDto
from app.clients.auth_users import InstructorDto
from app.clients.location import RoomDto

_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def load_rooms() -> list[RoomDto]:
    path = _DIR / "rooms.csv"
    out: list[RoomDto] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = int(row["room_id"])
            name = row["name"]
            cap = int(row["capacity"])
            out.append(
                RoomDto.model_validate(
                    {
                        "id": rid,
                        "name": name,
                        "number": name,
                        "capacity": cap,
                        "roomType": "Classroom",
                        "buildingId": 1,
                    }
                )
            )
    return out


@lru_cache(maxsize=1)
def load_instructors() -> list[InstructorDto]:
    path = _DIR / "instructors.csv"
    out: list[InstructorDto] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_id = (row.get("instructor_user_id") or "").strip()
            full_name = (row.get("full_name") or "").strip()
            # Backward-compat: tolerate malformed rows exported as '"1,""Last, First"""'.
            if raw_id and not full_name and "," in raw_id:
                left, right = raw_id.split(",", 1)
                raw_id = left.strip().strip('"')
                full_name = right.strip().strip('"')
            out.append(
                InstructorDto.model_validate(
                    {"id": raw_id, "fullName": full_name}
                )
            )
    return sorted(out, key=lambda x: (0, int(x.id)) if x.id.isdigit() else (1, x.id))


@lru_cache(maxsize=1)
def load_lessons() -> list[SchedulingLessonDto]:
    path = _DIR / "lessons.csv"
    out: list[SchedulingLessonDto] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(
                SchedulingLessonDto.model_validate(
                    {
                        "lessonId": int(row["lesson_id"]),
                        "instructorUserId": int(row["instructor_user_id"]),
                        "enrollment": 0,
                        "maxCapacity": int(row["available_seats"]),
                        "timesPerWeek": int(row["lessons_per_week"]),
                        "courseCode": row["course_number"],
                        "courseTitle": row["course_title"],
                        "lessonType": "Section",
                    }
                )
            )
    return out


def clear_mock_cache() -> None:
    load_rooms.cache_clear()
    load_instructors.cache_clear()
    load_lessons.cache_clear()

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.clients.attendance_headers import attendance_auth_headers
from app.core.config import settings
from app.core.errors import UpstreamError
from app.core.user_ids import normalize_instructor_user_id


class SchedulingLessonDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    lesson_id: int = Field(alias="lessonId")
    instructor_user_id: str = Field(alias="instructorUserId")

    @field_validator("instructor_user_id", mode="before")
    @classmethod
    def _coerce_instructor_user_id(cls, v: Any) -> str:
        if v is None:
            raise ValueError("instructorUserId is required")
        return normalize_instructor_user_id(v)
    enrollment: int = 0
    max_capacity: int = Field(default=0, alias="maxCapacity")
    times_per_week: int = Field(alias="timesPerWeek")
    course_code: str = Field(alias="courseCode")
    course_title: str = Field(alias="courseTitle")
    # Attendance scheduling payload may omit this; scheduler does not use it.
    lesson_type: str = Field(default="Section", alias="lessonType")


class AttendanceSchedulingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status_code: int | None = Field(default=None, alias="statusCode")
    message: str | None = None
    result: list[SchedulingLessonDto] = Field(default_factory=list)


def _lessons_from_attendance_json(data: Any) -> list[SchedulingLessonDto]:
    """Normalize Attendance API JSON to a list of scheduling lessons (several wrapper shapes)."""
    if isinstance(data, list):
        return [SchedulingLessonDto.model_validate(x) for x in data]
    if not isinstance(data, dict):
        raise UpstreamError("Unexpected Attendance lessons/scheduling response: not an object or array")

    for key in ("result", "lessons", "data", "items"):
        inner = data.get(key)
        if isinstance(inner, list):
            return [SchedulingLessonDto.model_validate(x) for x in inner]
        if isinstance(inner, dict):
            return [SchedulingLessonDto.model_validate(inner)]

    if "result" in data or "statusCode" in data or "message" in data:
        parsed = AttendanceSchedulingResponse.model_validate(data)
        return parsed.result

    raise UpstreamError("Unexpected Attendance lessons/scheduling response shape (expected list or wrapped array)")


def fetch_lessons_for_scheduling() -> list[SchedulingLessonDto]:
    if settings.use_mock_data:
        from app.mock_data.reader import load_lessons

        return load_lessons()

    url = f"{settings.attendance_base_url.rstrip('/')}/api/admin/lessons/scheduling"
    try:
        with httpx.Client(timeout=settings.http_timeout_seconds) as client:
            r = client.get(url, headers=attendance_auth_headers())
            if r.status_code >= 400:
                raise UpstreamError(f"Attendance service error: {r.status_code} {r.text[:500]}")
            data = r.json()
    except httpx.ConnectError as e:
        raise UpstreamError(
            f"Cannot connect to Attendance at {url} ({e}). "
            "Start the Attendance API on that host/port, or set ATTENDANCE_BASE_URL. "
            "For Docker→host on Windows/macOS the default is host.docker.internal. "
            "To skip external services locally, set USE_MOCK_DATA=true."
        ) from e
    except httpx.TimeoutException as e:
        raise UpstreamError(f"Attendance request timed out: {url}") from e
    return _lessons_from_attendance_json(data)

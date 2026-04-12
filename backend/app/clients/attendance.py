import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.errors import UpstreamError


class SchedulingLessonDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lesson_id: int = Field(alias="lessonId")
    instructor_user_id: int = Field(alias="instructorUserId")
    enrollment: int = 0
    max_capacity: int = Field(default=0, alias="maxCapacity")
    times_per_week: int = Field(alias="timesPerWeek")
    course_code: str = Field(alias="courseCode")
    course_title: str = Field(alias="courseTitle")
    lesson_type: str = Field(alias="lessonType")


class AttendanceSchedulingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status_code: int | None = Field(default=None, alias="statusCode")
    message: str | None = None
    result: list[SchedulingLessonDto] = Field(default_factory=list)


def fetch_lessons_for_scheduling() -> list[SchedulingLessonDto]:
    if settings.use_mock_data:
        from app.mock_data.reader import load_lessons

        return load_lessons()

    url = f"{settings.attendance_base_url.rstrip('/')}/api/admin/lessons/scheduling"
    with httpx.Client(timeout=settings.http_timeout_seconds) as client:
        r = client.get(url)
        if r.status_code >= 400:
            raise UpstreamError(f"Attendance service error: {r.status_code} {r.text[:500]}")
        data = r.json()
    parsed = AttendanceSchedulingResponse.model_validate(data)
    return parsed.result

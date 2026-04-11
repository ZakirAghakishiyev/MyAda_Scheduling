from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ScheduleGenerateRequest(BaseModel):
    academic_year: str = Field(..., min_length=1, max_length=32)
    semester: str = Field(..., min_length=1, max_length=32)


class SessionOut(BaseModel):
    id: int
    lesson_id: int
    instructor_user_id: int
    room_id: int
    room_name: str
    timeslot_id: str
    day: str
    start_time: str
    end_time: str
    preference_match: bool
    sequence_index: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    enrollment: int = 0
    room_capacity: int = 0

    model_config = {"from_attributes": True}


class UnscheduledOut(BaseModel):
    id: int
    lesson_id: int
    instructor_user_id: int
    times_per_week: int
    sessions_assigned: int
    sessions_needed: int
    reason: str
    partial_sessions: Optional[list[Any]] = None
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    enrollment: int = 0

    model_config = {"from_attributes": True}


class ScheduleSummary(BaseModel):
    total_lessons: int
    scheduled_lesson_count: int
    unscheduled_lesson_count: int
    scheduled_session_count: int
    preference_match_sessions: int


class ScheduleGenerateResponse(BaseModel):
    schedule_run_id: int
    status: str
    academic_year: str
    semester: str
    summary: ScheduleSummary
    scheduled_sessions: list[SessionOut]
    unscheduled_lessons: list[UnscheduledOut]


class ScheduleRunDetailResponse(BaseModel):
    id: int
    academic_year: str
    semester: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    summary: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class SessionPatchRequest(BaseModel):
    room_id: Optional[int] = None
    timeslot_id: Optional[str] = None


class SessionPatchResponse(BaseModel):
    session: SessionOut
    message: str = "Updated"


class SessionOptionsResponse(BaseModel):
    options: list[dict[str, Any]]


class PublishResponse(BaseModel):
    schedule_run_id: int
    status: str

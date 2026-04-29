"""Calls Attendance service bulk session generation (admin API)."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.clients.attendance_headers import attendance_auth_headers
from app.core.config import settings
from app.core.errors import UpstreamError


class WeeklySessionSlotPayload(BaseModel):
    """JSON body fragment for Attendance API (camelCase)."""

    model_config = ConfigDict(populate_by_name=True)

    day_of_week: str = Field(alias="dayOfWeek")
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")


def _unwrap_result(data: Any) -> dict[str, Any]:
    if isinstance(data, dict) and isinstance(data.get("result"), dict):
        return data["result"]
    if isinstance(data, dict):
        return data
    return {}


class BulkGenerateSessionsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    created_count: int = Field(default=0, alias="createdCount")
    skipped_duplicate_count: int = Field(default=0, alias="skippedDuplicateCount")


def bulk_generate_lesson_sessions(
    lesson_id: int,
    from_date: date,
    to_date: date,
    weekly_slots: list[WeeklySessionSlotPayload],
    topic: Optional[str] = None,
) -> BulkGenerateSessionsResponse:
    """POST /api/admin/lessons/{lessonId}/sessions/generate on Attendance service."""
    base = settings.attendance_base_url.rstrip("/")
    url = f"{base}/api/admin/lessons/{lesson_id}/sessions/generate"
    body: dict[str, Any] = {
        "fromDate": from_date.isoformat(),
        "toDate": to_date.isoformat(),
        "weeklySlots": [slot.model_dump(by_alias=True, exclude_none=True) for slot in weekly_slots],
    }
    if topic is not None:
        body["topic"] = topic

    with httpx.Client(timeout=settings.http_timeout_seconds) as client:
        r = client.post(url, json=body, headers=attendance_auth_headers())
        if r.status_code >= 400:
            raise UpstreamError(
                f"Attendance session generate failed for lesson {lesson_id}: "
                f"{r.status_code} {r.text[:800]}"
            )
        raw = r.json()
    unwrapped = _unwrap_result(raw)
    return BulkGenerateSessionsResponse.model_validate(unwrapped)

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PreferenceProfileResponse(BaseModel):
    id: int
    instructor_user_id: int
    academic_year: str
    semester: str
    strict: bool
    notes: Optional[str] = None
    preferred_days: list[str] = Field(default_factory=list)
    preferred_time_categories: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PreferenceProfileUpsert(BaseModel):
    academic_year: str = Field(..., min_length=1, max_length=32)
    semester: str = Field(..., min_length=1, max_length=32)
    strict: bool = False
    notes: Optional[str] = None
    preferred_days: list[str] = Field(default_factory=list)
    preferred_time_categories: list[str] = Field(default_factory=list)

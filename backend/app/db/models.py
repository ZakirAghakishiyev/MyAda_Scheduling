import enum
from datetime import datetime, timezone
from typing import Any, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScheduleRunStatus(str, enum.Enum):
    draft = "draft"
    running = "running"
    completed = "completed"
    failed = "failed"
    published = "published"


class ScheduleChangeAction(str, enum.Enum):
    manual_patch = "manual_patch"
    publish = "publish"


class InstructorPreferenceProfile(Base):
    __tablename__ = "instructor_preference_profiles"
    __table_args__ = (
        UniqueConstraint(
            "instructor_user_id",
            "academic_year",
            "semester",
            name="uq_pref_profile_instructor_year_semester",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instructor_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    academic_year: Mapped[str] = mapped_column(String(32), nullable=False)
    semester: Mapped[str] = mapped_column(String(32), nullable=False)
    strict_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    days: Mapped[list["InstructorPreferenceDay"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    times: Mapped[list["InstructorPreferenceTime"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class InstructorPreferenceDay(Base):
    __tablename__ = "instructor_preference_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("instructor_preference_profiles.id", ondelete="CASCADE"), nullable=False
    )
    day_name: Mapped[str] = mapped_column(String(16), nullable=False)

    profile: Mapped["InstructorPreferenceProfile"] = relationship(back_populates="days")


class InstructorPreferenceTime(Base):
    __tablename__ = "instructor_preference_times"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("instructor_preference_profiles.id", ondelete="CASCADE"), nullable=False
    )
    time_category: Mapped[str] = mapped_column(String(32), nullable=False)

    profile: Mapped["InstructorPreferenceProfile"] = relationship(back_populates="times")


class ScheduleRun(Base):
    __tablename__ = "schedule_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    academic_year: Mapped[str] = mapped_column(String(32), nullable=False)
    semester: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=ScheduleRunStatus.draft.value)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    sessions: Mapped[list["ScheduledSession"]] = relationship(
        back_populates="schedule_run", cascade="all, delete-orphan"
    )
    unscheduled: Mapped[list["UnscheduledLesson"]] = relationship(
        back_populates="schedule_run", cascade="all, delete-orphan"
    )
    change_logs: Mapped[list["ScheduleChangeLog"]] = relationship(
        back_populates="schedule_run", cascade="all, delete-orphan"
    )


Index("ix_schedule_runs_year_semester", ScheduleRun.academic_year, ScheduleRun.semester)


class ScheduledSession(Base):
    __tablename__ = "scheduled_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_run_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    instructor_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    room_id: Mapped[int] = mapped_column(Integer, nullable=False)
    room_name: Mapped[str] = mapped_column(String(256), nullable=False)
    timeslot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    day: Mapped[str] = mapped_column(String(32), nullable=False)
    start_time: Mapped[str] = mapped_column(String(16), nullable=False)
    end_time: Mapped[str] = mapped_column(String(16), nullable=False)
    preference_match: Mapped[bool] = mapped_column(Boolean, default=False)
    sequence_index: Mapped[int] = mapped_column(Integer, default=0)
    course_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    course_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    enrollment: Mapped[int] = mapped_column(Integer, default=0)
    room_capacity: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    schedule_run: Mapped["ScheduleRun"] = relationship(back_populates="sessions")
    change_logs: Mapped[list["ScheduleChangeLog"]] = relationship(back_populates="session")


Index(
    "ix_scheduled_sessions_run_instructor_slot",
    ScheduledSession.schedule_run_id,
    ScheduledSession.instructor_user_id,
    ScheduledSession.timeslot_id,
)
Index(
    "ix_scheduled_sessions_run_room_slot",
    ScheduledSession.schedule_run_id,
    ScheduledSession.room_id,
    ScheduledSession.timeslot_id,
)


class UnscheduledLesson(Base):
    __tablename__ = "unscheduled_lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_run_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[int] = mapped_column(Integer, nullable=False)
    instructor_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    times_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    sessions_assigned: Mapped[int] = mapped_column(Integer, nullable=False)
    sessions_needed: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    partial_sessions: Mapped[Optional[list[Any]]] = mapped_column(JSONB, nullable=True)
    course_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    course_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    enrollment: Mapped[int] = mapped_column(Integer, default=0)


class ScheduleChangeLog(Base):
    __tablename__ = "schedule_change_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_run_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("scheduled_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    before_state: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    schedule_run: Mapped["ScheduleRun"] = relationship(back_populates="change_logs")
    session: Mapped[Optional["ScheduledSession"]] = relationship(back_populates="change_logs")

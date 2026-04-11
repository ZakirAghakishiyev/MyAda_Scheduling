"""initial_schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-04-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instructor_preference_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instructor_user_id", sa.Integer(), nullable=False),
        sa.Column("academic_year", sa.String(length=32), nullable=False),
        sa.Column("semester", sa.String(length=32), nullable=False),
        sa.Column("strict_mode", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instructor_user_id",
            "academic_year",
            "semester",
            name="uq_pref_profile_instructor_year_semester",
        ),
    )
    op.create_index(
        op.f("ix_instructor_preference_profiles_instructor_user_id"),
        "instructor_preference_profiles",
        ["instructor_user_id"],
        unique=False,
    )

    op.create_table(
        "instructor_preference_days",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("day_name", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["instructor_preference_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "instructor_preference_times",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("time_category", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["instructor_preference_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "schedule_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("academic_year", sa.String(length=32), nullable=False),
        sa.Column("semester", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_schedule_runs_year_semester", "schedule_runs", ["academic_year", "semester"], unique=False)

    op.create_table(
        "scheduled_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("schedule_run_id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("instructor_user_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("room_name", sa.String(length=256), nullable=False),
        sa.Column("timeslot_id", sa.String(length=64), nullable=False),
        sa.Column("day", sa.String(length=32), nullable=False),
        sa.Column("start_time", sa.String(length=16), nullable=False),
        sa.Column("end_time", sa.String(length=16), nullable=False),
        sa.Column("preference_match", sa.Boolean(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("course_code", sa.String(length=64), nullable=True),
        sa.Column("course_title", sa.String(length=512), nullable=True),
        sa.Column("enrollment", sa.Integer(), nullable=False),
        sa.Column("room_capacity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["schedule_run_id"], ["schedule_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_scheduled_sessions_schedule_run_id"),
        "scheduled_sessions",
        ["schedule_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_sessions_lesson_id"),
        "scheduled_sessions",
        ["lesson_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_sessions_instructor_user_id"),
        "scheduled_sessions",
        ["instructor_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_sessions_run_instructor_slot",
        "scheduled_sessions",
        ["schedule_run_id", "instructor_user_id", "timeslot_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_sessions_run_room_slot",
        "scheduled_sessions",
        ["schedule_run_id", "room_id", "timeslot_id"],
        unique=False,
    )

    op.create_table(
        "unscheduled_lessons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("schedule_run_id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("instructor_user_id", sa.Integer(), nullable=False),
        sa.Column("times_per_week", sa.Integer(), nullable=False),
        sa.Column("sessions_assigned", sa.Integer(), nullable=False),
        sa.Column("sessions_needed", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("partial_sessions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("course_code", sa.String(length=64), nullable=True),
        sa.Column("course_title", sa.String(length=512), nullable=True),
        sa.Column("enrollment", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["schedule_run_id"], ["schedule_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_unscheduled_lessons_schedule_run_id"),
        "unscheduled_lessons",
        ["schedule_run_id"],
        unique=False,
    )

    op.create_table(
        "schedule_change_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("schedule_run_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["schedule_run_id"], ["schedule_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["scheduled_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_schedule_change_logs_schedule_run_id"),
        "schedule_change_logs",
        ["schedule_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_schedule_change_logs_session_id"),
        "schedule_change_logs",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("schedule_change_logs")
    op.drop_table("unscheduled_lessons")
    op.drop_table("scheduled_sessions")
    op.drop_table("schedule_runs")
    op.drop_table("instructor_preference_times")
    op.drop_table("instructor_preference_days")
    op.drop_table("instructor_preference_profiles")

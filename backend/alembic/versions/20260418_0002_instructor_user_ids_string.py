"""instructor and actor user ids as string (Auth GUIDs)

Revision ID: 0002_instructor_str
Revises: 0001_initial
Create Date: 2026-04-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_instructor_str"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "instructor_preference_profiles",
        "instructor_user_id",
        existing_type=sa.Integer(),
        type_=sa.String(length=64),
        existing_nullable=False,
        postgresql_using="instructor_user_id::text",
    )
    op.alter_column(
        "scheduled_sessions",
        "instructor_user_id",
        existing_type=sa.Integer(),
        type_=sa.String(length=64),
        existing_nullable=False,
        postgresql_using="instructor_user_id::text",
    )
    op.alter_column(
        "unscheduled_lessons",
        "instructor_user_id",
        existing_type=sa.Integer(),
        type_=sa.String(length=64),
        existing_nullable=False,
        postgresql_using="instructor_user_id::text",
    )
    op.alter_column(
        "schedule_change_logs",
        "actor_user_id",
        existing_type=sa.Integer(),
        type_=sa.String(length=64),
        existing_nullable=False,
        postgresql_using="actor_user_id::text",
    )


def downgrade() -> None:
    # Lossy if non-numeric ids were stored; prefer restoring from backup.
    pass

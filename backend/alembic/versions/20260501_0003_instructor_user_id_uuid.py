"""store instructor_user_id as PostgreSQL uuid

Revision ID: 0003_instructor_uuid
Revises: 0002_instructor_str
Create Date: 2026-05-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.user_ids import normalize_instructor_user_id

revision: str = "0003_instructor_uuid"
down_revision: Union[str, None] = "0002_instructor_str"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _migrate_table(bind: sa.Connection, table: str, pk_col: str) -> None:
    tmp = "instructor_user_id_uuid"
    op.add_column(
        table,
        sa.Column(tmp, postgresql.UUID(as_uuid=False), nullable=True),
    )
    rows = bind.execute(sa.text(f"SELECT {pk_col}, instructor_user_id FROM {table}")).fetchall()
    for pk, old in rows:
        nu = normalize_instructor_user_id(old)
        bind.execute(
            sa.text(f"UPDATE {table} SET {tmp} = CAST(:u AS uuid) WHERE {pk_col} = :pk"),
            {"u": nu, "pk": pk},
        )
    op.drop_column(table, "instructor_user_id")
    op.execute(sa.text(f"ALTER TABLE {table} RENAME COLUMN {tmp} TO instructor_user_id"))
    op.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN instructor_user_id SET NOT NULL"))


def upgrade() -> None:
    op.drop_constraint(
        "uq_pref_profile_instructor_year_semester",
        "instructor_preference_profiles",
        type_="unique",
    )
    op.drop_index(
        op.f("ix_instructor_preference_profiles_instructor_user_id"),
        table_name="instructor_preference_profiles",
    )
    op.drop_index(
        op.f("ix_scheduled_sessions_instructor_user_id"),
        table_name="scheduled_sessions",
    )
    op.drop_index("ix_scheduled_sessions_run_instructor_slot", table_name="scheduled_sessions")

    bind = op.get_bind()
    assert bind is not None
    _migrate_table(bind, "instructor_preference_profiles", "id")
    _migrate_table(bind, "scheduled_sessions", "id")
    _migrate_table(bind, "unscheduled_lessons", "id")

    op.create_index(
        op.f("ix_instructor_preference_profiles_instructor_user_id"),
        "instructor_preference_profiles",
        ["instructor_user_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_pref_profile_instructor_year_semester",
        "instructor_preference_profiles",
        ["instructor_user_id", "academic_year", "semester"],
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


def downgrade() -> None:
    pass

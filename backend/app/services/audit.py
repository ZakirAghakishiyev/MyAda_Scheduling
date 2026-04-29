from sqlalchemy.orm import Session

from app.db.models import ScheduleChangeLog


def log_change(
    db: Session,
    *,
    schedule_run_id: int,
    session_id: int | None,
    actor_user_id: str,
    action: str,
    before_state: dict | None,
    after_state: dict | None,
) -> None:
    db.add(
        ScheduleChangeLog(
            schedule_run_id=schedule_run_id,
            session_id=session_id,
            actor_user_id=actor_user_id,
            action=action,
            before_state=before_state,
            after_state=after_state,
        )
    )

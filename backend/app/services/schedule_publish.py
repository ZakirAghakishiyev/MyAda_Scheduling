from sqlalchemy.orm import Session

from app.core.errors import ValidationAppError
from app.db.models import ScheduleRunStatus
from app.schemas.schedule import PublishResponse
from app.services import audit as audit_service
from app.services.schedule_query import get_run_or_404


def publish_schedule(db: Session, schedule_run_id: int, actor_user_id: int) -> PublishResponse:
    run = get_run_or_404(db, schedule_run_id)
    if run.status != ScheduleRunStatus.completed.value:
        raise ValidationAppError("Only a completed schedule run can be published")
    prev = run.status
    run.status = ScheduleRunStatus.published.value
    audit_service.log_change(
        db,
        schedule_run_id=schedule_run_id,
        session_id=None,
        actor_user_id=actor_user_id,
        action="publish",
        before_state={"status": prev},
        after_state={"status": run.status},
    )
    db.commit()
    db.refresh(run)
    return PublishResponse(schedule_run_id=run.id, status=run.status)

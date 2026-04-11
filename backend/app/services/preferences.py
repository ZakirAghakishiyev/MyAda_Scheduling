from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    InstructorPreferenceDay,
    InstructorPreferenceProfile,
    InstructorPreferenceTime,
)
from app.schemas.preferences import PreferenceProfileResponse, PreferenceProfileUpsert
from app.scheduler.engine import PreferenceInput


def get_profile(
    db: Session, instructor_user_id: int, academic_year: str, semester: str
) -> InstructorPreferenceProfile | None:
    return db.execute(
        select(InstructorPreferenceProfile).where(
            InstructorPreferenceProfile.instructor_user_id == instructor_user_id,
            InstructorPreferenceProfile.academic_year == academic_year,
            InstructorPreferenceProfile.semester == semester,
        )
    ).scalar_one_or_none()


def to_response(p: InstructorPreferenceProfile) -> PreferenceProfileResponse:
    days = [d.day_name for d in p.days]
    times = [t.time_category for t in p.times]
    return PreferenceProfileResponse(
        id=p.id,
        instructor_user_id=p.instructor_user_id,
        academic_year=p.academic_year,
        semester=p.semester,
        strict=p.strict_mode,
        notes=p.notes,
        preferred_days=days,
        preferred_time_categories=times,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def upsert_profile(
    db: Session, instructor_user_id: int, body: PreferenceProfileUpsert
) -> InstructorPreferenceProfile:
    existing = get_profile(db, instructor_user_id, body.academic_year, body.semester)
    if existing:
        existing.strict_mode = body.strict
        existing.notes = body.notes
        db.flush()
        db.execute(delete(InstructorPreferenceDay).where(InstructorPreferenceDay.profile_id == existing.id))
        db.execute(delete(InstructorPreferenceTime).where(InstructorPreferenceTime.profile_id == existing.id))
        for d in body.preferred_days:
            db.add(InstructorPreferenceDay(profile_id=existing.id, day_name=d))
        for t in body.preferred_time_categories:
            db.add(InstructorPreferenceTime(profile_id=existing.id, time_category=t))
        db.commit()
        db.refresh(existing)
        return existing

    profile = InstructorPreferenceProfile(
        instructor_user_id=instructor_user_id,
        academic_year=body.academic_year,
        semester=body.semester,
        strict_mode=body.strict,
        notes=body.notes,
    )
    db.add(profile)
    db.flush()
    for d in body.preferred_days:
        db.add(InstructorPreferenceDay(profile_id=profile.id, day_name=d))
    for t in body.preferred_time_categories:
        db.add(InstructorPreferenceTime(profile_id=profile.id, time_category=t))
    db.commit()
    db.refresh(profile)
    return profile


def load_engine_preferences(
    db: Session, instructor_user_ids: set[int], academic_year: str, semester: str
) -> list[PreferenceInput]:
    if not instructor_user_ids:
        return []
    rows = db.execute(
        select(InstructorPreferenceProfile).where(
            InstructorPreferenceProfile.academic_year == academic_year,
            InstructorPreferenceProfile.semester == semester,
            InstructorPreferenceProfile.instructor_user_id.in_(instructor_user_ids),
        )
    ).scalars().all()
    out: list[PreferenceInput] = []
    for p in rows:
        out.append(
            {
                "instructor_user_id": p.instructor_user_id,
                "preferred_days": [d.day_name for d in p.days],
                "preferred_times": [t.time_category for t in p.times],
                "strict": p.strict_mode,
            }
        )
    return out

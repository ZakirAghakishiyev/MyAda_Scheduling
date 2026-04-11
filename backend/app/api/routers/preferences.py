from fastapi import APIRouter, Query

from app.api.deps import DbDep, UserIdDep
from app.core.errors import NotFoundError, http_not_found
from app.schemas.preferences import PreferenceProfileResponse, PreferenceProfileUpsert
from app.services import preferences as pref_service

router = APIRouter(prefix="/instructors/me", tags=["instructor-preferences"])


@router.get("/preferences", response_model=PreferenceProfileResponse)
def get_my_preferences(
    db: DbDep,
    user_id: UserIdDep,
    academic_year: str = Query(..., min_length=1),
    semester: str = Query(..., min_length=1),
) -> PreferenceProfileResponse:
    p = pref_service.get_profile(db, user_id, academic_year, semester)
    if not p:
        raise http_not_found(NotFoundError("No preference profile for this term")) from None
    return pref_service.to_response(p)


@router.put("/preferences", response_model=PreferenceProfileResponse)
def put_my_preferences(
    db: DbDep,
    user_id: UserIdDep,
    body: PreferenceProfileUpsert,
) -> PreferenceProfileResponse:
    p = pref_service.upsert_profile(db, user_id, body)
    return pref_service.to_response(p)

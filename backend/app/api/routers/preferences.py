from fastapi import APIRouter, Depends, Query

from app.api.deps import DbDep, UserIdDep
from app.clients.attendance_headers import bind_optional_upstream_bearer
from app.core.config import settings
from app.core.errors import NotFoundError, http_not_found
from app.schemas.preferences import PreferenceProfileResponse, PreferenceProfileUpsert
from app.services import preferences as pref_service

router = APIRouter(
    prefix="/instructors",
    tags=["instructor-preferences"],
    dependencies=[Depends(bind_optional_upstream_bearer)],
)


@router.get(
    "/preferences",
    response_model=PreferenceProfileResponse,
    summary="Get instructor preferences",
    operation_id="get_instructor_preferences",
    description=(
        f"Instructor is identified by the `{settings.dev_user_id_header}` header "
        "(Auth user UUID or legacy numeric id string)."
    ),
)
def get_preferences(
    db: DbDep,
    user_id: UserIdDep,
    academic_year: str = Query(..., min_length=1),
    semester: str = Query(..., min_length=1),
) -> PreferenceProfileResponse:
    p = pref_service.get_profile(db, user_id, academic_year, semester)
    if not p:
        raise http_not_found(NotFoundError("No preference profile for this term")) from None
    return pref_service.to_response(p)


@router.post(
    "/preferences",
    response_model=PreferenceProfileResponse,
    summary="Create or replace instructor preferences (POST)",
    operation_id="post_instructor_preferences",
    description=(
        f"Upserts profile for `(academic_year, semester)`. "
        f"Instructor id: `{settings.dev_user_id_header}` (UUID or numeric string)."
    ),
)
def post_preferences(
    db: DbDep,
    user_id: UserIdDep,
    body: PreferenceProfileUpsert,
) -> PreferenceProfileResponse:
    p = pref_service.upsert_profile(db, user_id, body)
    return pref_service.to_response(p)


@router.put(
    "/preferences",
    response_model=PreferenceProfileResponse,
    summary="Create or replace instructor preferences (PUT)",
    operation_id="put_instructor_preferences",
    description=(
        f"Same behavior as POST. Instructor id: `{settings.dev_user_id_header}` (UUID or numeric string)."
    ),
)
def put_preferences(
    db: DbDep,
    user_id: UserIdDep,
    body: PreferenceProfileUpsert,
) -> PreferenceProfileResponse:
    p = pref_service.upsert_profile(db, user_id, body)
    return pref_service.to_response(p)

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.errors import UpstreamError

INSTRUCTOR_ROLE = "Instructor"


class InstructorDto(BaseModel):
    """Instructor identity from Auth (id is typically a GUID string) or mock CSV."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    full_name: str = Field(alias="fullName")


class AuthUserListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    user_name: str = Field(alias="userName")
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")


class UsersByRoleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    role: str
    count: int
    users: list[AuthUserListItem] = Field(default_factory=list)


def _auth_users_by_role_url(base: str, role: str) -> str:
    b = base.rstrip("/")
    if b.endswith("/api/auth"):
        return f"{b}/users-by-role/{role}"
    return f"{b}/api/auth/users-by-role/{role}"


def _instructor_from_auth_user(u: AuthUserListItem) -> InstructorDto:
    fn = (u.first_name or "").strip()
    ln = (u.last_name or "").strip()
    full = f"{fn} {ln}".strip() or u.user_name
    return InstructorDto(id=u.id, fullName=full)


def fetch_instructors() -> list[InstructorDto]:
    if settings.use_mock_data:
        from app.mock_data.reader import load_instructors

        return load_instructors()

    token = (settings.auth_service_access_token or "").strip()
    if not token:
        raise UpstreamError(
            "AUTH_SERVICE_ACCESS_TOKEN is required to list instructors from Auth "
            "(GET /api/auth/users-by-role/Instructor is admin-protected). "
            "Set the token, or enable USE_MOCK_DATA."
        )

    url = _auth_users_by_role_url(settings.auth_base_url, INSTRUCTOR_ROLE)
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=settings.http_timeout_seconds) as client:
        r = client.get(url, headers=headers)
        if r.status_code >= 400:
            raise UpstreamError(f"Auth service error: {r.status_code} {r.text[:500]}")
        raw = r.json()
    parsed = UsersByRoleResponse.model_validate(raw)
    return [_instructor_from_auth_user(u) for u in parsed.users]

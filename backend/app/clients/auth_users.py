import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.errors import UpstreamError

INSTRUCTOR_ROLE = "Instructor"


class InstructorDto(BaseModel):
    """Instructor identity from Auth (id is typically a GUID string)."""

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
    # Prefer explicit service token; fall back to per-request Bearer from Scheduling Swagger (if present).
    token = (settings.auth_service_access_token or "").strip()
    if not token:
        try:
            # Reuse the per-request token bound by bind_optional_upstream_bearer.
            from app.clients.attendance_headers import _upstream_request_token  # type: ignore

            token = (_upstream_request_token.get() or "").strip()
        except Exception:
            token = ""

    if not token:
        raise UpstreamError(
            "AUTH_SERVICE_ACCESS_TOKEN is required to list instructors from Auth "
            "(GET /api/auth/users-by-role/Instructor is admin-protected). "
            "Set the token, or pass Authorization Bearer from this API when calling generate."
        )

    url = _auth_users_by_role_url(settings.auth_base_url, INSTRUCTOR_ROLE)
    if token.lower().startswith("bearer "):
        headers = {"Authorization": token}
    else:
        headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=settings.http_timeout_seconds) as client:
        r = client.get(url, headers=headers)
        if r.status_code >= 400:
            raise UpstreamError(f"Auth service error: {r.status_code} {r.text[:500]}")
        raw = r.json()
    parsed = UsersByRoleResponse.model_validate(raw)
    return [_instructor_from_auth_user(u) for u in parsed.users]

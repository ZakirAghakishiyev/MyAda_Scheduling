import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.errors import UpstreamError


class InstructorDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    full_name: str = Field(alias="fullName")


def fetch_instructors() -> list[InstructorDto]:
    if settings.use_mock_data:
        from app.mock_data.reader import load_instructors

        return load_instructors()

    url = f"{settings.auth_base_url.rstrip('/')}/api/v1/instructors"
    with httpx.Client(timeout=settings.http_timeout_seconds) as client:
        r = client.get(url)
        if r.status_code >= 400:
            raise UpstreamError(f"Auth service error: {r.status_code} {r.text[:500]}")
        raw = r.json()
    if isinstance(raw, list):
        return [InstructorDto.model_validate(x) for x in raw]
    if isinstance(raw, dict) and "result" in raw:
        return [InstructorDto.model_validate(x) for x in raw["result"]]
    raise UpstreamError("Unexpected Auth instructors response shape")

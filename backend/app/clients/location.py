import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.errors import UpstreamError


class RoomDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    number: str | None = None
    capacity: int
    room_type: str | int | None = Field(default=None, alias="roomType")
    building_id: int = Field(alias="buildingId")


def fetch_rooms() -> list[RoomDto]:
    url = f"{settings.location_base_url.rstrip('/')}/api/v1/rooms"
    with httpx.Client(timeout=settings.http_timeout_seconds) as client:
        r = client.get(url)
        if r.status_code >= 400:
            raise UpstreamError(f"Location service error: {r.status_code} {r.text[:500]}")
        raw = r.json()
    if isinstance(raw, list):
        return [RoomDto.model_validate(x) for x in raw]
    if isinstance(raw, dict) and "result" in raw:
        return [RoomDto.model_validate(x) for x in raw["result"]]
    raise UpstreamError("Unexpected Location rooms response shape")

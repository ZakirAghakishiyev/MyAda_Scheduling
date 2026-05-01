"""HTTP client for LocationService rooms.

Configure ``settings.location_base_url`` to the API root including ``/api/v1``:

- **Gateway:** ``http://<host>:5000/location/api/v1`` → ``GET .../rooms`` lists rooms (anonymous).
- **Direct:** ``http://localhost:5005/api/v1`` if calling LocationService without gateway.
"""

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.errors import UpstreamError


class RoomDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: int
    name: str
    number: str | None = None
    capacity: int
    room_type: str | int | None = Field(default=None, alias="roomType")
    building_id: int = Field(alias="buildingId")
    building_name: str | None = Field(default=None, alias="buildingName")


def _location_rooms_url(base: str) -> str:
    b = base.rstrip("/")
    if b.endswith("/api/v1"):
        return f"{b}/rooms"
    return f"{b}/api/v1/rooms"


def _rooms_from_location_json(data: Any) -> list[RoomDto]:
    if isinstance(data, list):
        return [RoomDto.model_validate(x) for x in data]
    if isinstance(data, dict):
        for key in ("result", "rooms", "data", "items"):
            inner = data.get(key)
            if isinstance(inner, list):
                return [RoomDto.model_validate(x) for x in inner]
    raise UpstreamError("Unexpected Location /rooms response shape")


def fetch_rooms() -> list[RoomDto]:
    url = _location_rooms_url(settings.location_base_url)
    try:
        with httpx.Client(timeout=settings.http_timeout_seconds) as client:
            r = client.get(url)
            if r.status_code >= 400:
                raise UpstreamError(f"Location service error: {r.status_code} {r.text[:500]}")
            raw = r.json()
    except httpx.ConnectError as e:
        raise UpstreamError(
            f"Cannot connect to Location at {url} ({e}). "
            "Check LOCATION_BASE_URL and that the service is reachable from this process."
        ) from e
    except httpx.TimeoutException as e:
        raise UpstreamError(f"Location request timed out: {url}") from e
    return _rooms_from_location_json(raw)

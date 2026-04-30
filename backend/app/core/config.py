from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5431/scheduling"
    attendance_base_url: str = "https://myada.site/attendance"
    # Bearer (or full "Bearer …") sent on every server-side request to Attendance
    attendance_access_token: str = Field(default="", alias="ATTENDANCE_ACCESS_TOKEN")
    # LocationService JSON root. Gateway: host + /location/api/v1 (gateway strips /location when forwarding).
    # Rooms list: {location_base_url}/rooms  e.g. http://host:5000/location/api/v1/rooms
    location_base_url: str = "https://myada.site/location/api/v1"
    # Auth: host only or gateway root, e.g. http://localhost:5001 or http://localhost:5000
    # Deployed gateway example: https://myada.site/auth (backend calls /api/auth/... under this base)
    auth_base_url: str = "https://myada.site/auth"
    # Admin access token for server-side GET /api/auth/users-by-role/{role} (instructors list)
    auth_service_access_token: str = Field(default="", alias="AUTH_SERVICE_ACCESS_TOKEN")
    http_timeout_seconds: float = 30.0
    dev_user_id_header: str = "X-User-Id"
    use_mock_data: bool = Field(default=False, alias="USE_MOCK_DATA")
    # Comma-separated origins, or "*" for any origin (credentials disabled for "*")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")


settings = Settings()


def cors_middleware_kwargs() -> dict:
    """Options for Starlette CORSMiddleware; applies to all routes."""
    raw = settings.cors_origins.strip()
    if not raw or raw == "*":
        return {
            "allow_origins": ["*"],
            "allow_credentials": False,
        }
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins:
        return {
            "allow_origins": ["*"],
            "allow_credentials": False,
        }
    return {
        "allow_origins": origins,
        "allow_credentials": True,
    }

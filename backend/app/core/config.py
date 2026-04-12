from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/scheduling"
    attendance_base_url: str = "http://localhost:5008"
    location_base_url: str = "http://localhost:5005"
    auth_base_url: str = "http://localhost:5001"
    http_timeout_seconds: float = 30.0
    dev_user_id_header: str = "X-User-Id"
    use_mock_data: bool = Field(default=False, alias="USE_MOCK_DATA")


settings = Settings()

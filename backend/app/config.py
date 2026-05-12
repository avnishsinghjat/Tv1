"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = next((p for p in (_REPO_ROOT / ".env", _BACKEND_ROOT / ".env") if p.is_file()), _REPO_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="teamcenter-analytics", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")

    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@db:5432/teamcenter_analytics",
        validation_alias="DATABASE_URL",
    )

    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")

    jwt_secret: str = Field(default="change-me-in-production", validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Demo users: "username:password_hash" uses bcrypt via passlib in auth route setup
    admin_username: str = Field(default="admin", validation_alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", validation_alias="ADMIN_PASSWORD")

    teamcenter_mock_mode: bool = Field(default=True, validation_alias="TEAMCENTER_MOCK_MODE")
    teamcenter_base_url: str = Field(default="", validation_alias="TEAMCENTER_BASE_URL")
    # Live Teamcenter REST (same host as AWC, e.g. http://tcappccmdev:3000)
    teamcenter_user: str = Field(default="", validation_alias="TEAMCENTER_USER")
    teamcenter_password: str = Field(default="", validation_alias="TEAMCENTER_PASSWORD")
    teamcenter_warmup_path: str = Field(default="/tc/RestServices", validation_alias="TEAMCENTER_WARMUP_PATH")
    teamcenter_login_path: str = Field(
        default="/tc/RestServices/Core-2011-06-Session/login",
        validation_alias="TEAMCENTER_LOGIN_PATH",
    )
    teamcenter_client_id: str = Field(default="ActiveWorkspaceClient", validation_alias="TEAMCENTER_CLIENT_ID")
    teamcenter_client_version: str = Field(default="10000.1.2", validation_alias="TEAMCENTER_CLIENT_VERSION")
    teamcenter_client_discriminator: str = Field(default="AWC13152", validation_alias="TEAMCENTER_CLIENT_DISCRIMINATOR")
    teamcenter_locale: str = Field(default="en_US", validation_alias="TEAMCENTER_LOCALE")
    # Optional extra GET paths (comma-separated, app-relative) after login, e.g. /tc/RestServices/...
    teamcenter_extra_get_paths_csv: str = Field(default="", validation_alias="TEAMCENTER_EXTRA_GET_PATHS")

    @computed_field
    @property
    def teamcenter_extra_get_paths(self) -> list[str]:
        return [p.strip() for p in self.teamcenter_extra_get_paths_csv.split(",") if p.strip()]

    # Comma-separated in .env (JSON list is not required).
    cors_origins_csv: str = Field(default="", validation_alias="CORS_ORIGINS")

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [p.strip() for p in self.cors_origins_csv.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

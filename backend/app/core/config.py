"""Application settings.

Centralized configuration loaded from environment variables (via a .env file
in local development). See backend/.env.example for all supported options.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Restaurant Catalog API.

    Values are read from environment variables (case-insensitive) and,
    for local dev, from a `.env` file placed in the `backend/` directory.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Restaurant Catalog API"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    # Database. Defaults to a local SQLite file for zero-config dev.
    # For production, set DATABASE_URL to an async Postgres DSN, e.g.:
    #   postgresql+asyncpg://user:password@host:5432/restaurant_catalog
    database_url: str = Field(default="sqlite+aiosqlite:///./restaurant_catalog.db")

    # JWT / password-flow auth
    secret_key: str = Field(default="CHANGE_ME_DEV_ONLY_INSECURE_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60 * 24)  # 24h, generous for a demo

    # CORS - the Vite dev server origin by default.
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    # Optional real OAuth2 (Google) config. When unset, Google login is
    # disabled and the API falls back to the OAuth2 password/JWT flow.
    # See README "Auth flow" section for how to enable this for real.
    google_client_id: str | None = Field(default=None)
    google_client_secret: str | None = Field(default=None)
    google_redirect_uri: str | None = Field(default=None)

    @property
    def google_oauth_configured(self) -> bool:
        return bool(
            self.google_client_id and self.google_client_secret and self.google_redirect_uri
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

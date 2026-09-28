# app/config.py
# A SINGLE place for the whole application configuration.
# Instead of calling os.getenv(...) across many files, we describe all settings
# as a Settings class. The pydantic-settings library loads values from the .env
# file, validates their types, and fails loudly at startup if something is missing.

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application settings in a single object.

    Each field below maps to an env variable of the same name in the .env file.
    """

    # --- Database ---
    # ": str" is a type annotation - it says "this value must be text".
    # No default value = REQUIRED field. If it is missing from .env,
    # the app won't start (which is good - we learn immediately what to fix).
    DATABASE_URL: str

    # --- API-Football ---
    API_FOOTBALL_KEY: str

    # This field HAS a default value (after "="), so it is optional in .env.
    # If nobody provides their own address, we use this one.
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"

    @field_validator("DATABASE_URL")
    @classmethod
    def normalise_database_url(cls, value: str) -> str:
        """Rewrite the legacy postgres:// scheme to the postgresql:// SQLAlchemy needs.

        Some hosting providers hand out connection strings starting with
        postgres://, which SQLAlchemy 2.0 rejects ("Can't load plugin") because it
        only knows the dialect name postgresql. Fixing it here - at load time -
        means every consumer (database.py, alembic/env.py) gets the usable value.
        The count of 1 makes sure we only touch the scheme, never a "postgres"
        that happens to appear inside the password or database name.
        """
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value

    # --- Admin / imports ---
    # Shared secret guarding the POST /import-* endpoints (see app/security.py).
    # Those endpoints spend our paid API-Football quota and write to the database,
    # so once the app is public they must not be open to everyone. No default on
    # purpose: a default would ship a secret that every reader of the repo knows.
    IMPORT_TOKEN: str

    # --- CORS ---
    # Browser origins allowed to call this API (i.e. our frontend). Stored as a
    # comma-separated string, not a list, because env variables are always plain
    # text - a hosting panel has no way to hand us a real Python list.
    # Default keeps local development working with no configuration at all.
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Split ALLOWED_ORIGINS into the clean list CORSMiddleware expects."""
        origins = []
        for origin in self.ALLOWED_ORIGINS.split(","):
            cleaned = origin.strip()
            if cleaned:
                origins.append(cleaned)
        return origins

    # model_config tells pydantic-settings where and how to read the settings.
    model_config = SettingsConfigDict(
        env_file=".env",  # read variables from this file
        env_file_encoding="utf-8",  # file encoding (accents, etc.)
        extra="ignore",  # extra variables in .env won't raise an error
    )


# We create ONE shared settings object. In other files we simply write:
#   from app.config import settings
# and access settings.DATABASE_URL, settings.API_FOOTBALL_KEY, etc.
settings = Settings()

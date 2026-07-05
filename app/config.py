# app/config.py
# A SINGLE place for the whole application configuration.
# Instead of calling os.getenv(...) across many files, we describe all settings
# as a Settings class. The pydantic-settings library loads values from the .env
# file, validates their types, and fails loudly at startup if something is missing.

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

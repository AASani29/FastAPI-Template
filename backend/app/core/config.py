"""Single source of truth for configuration.

Every tunable in the app is a field on `Settings`. Nothing reads os.environ
directly and no constant is defined at a call site, so there is exactly one
place to look when you want to know what a value is or change it.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py -> core -> app -> backend. Anchoring the .env path to this file
# instead of the process CWD means `uvicorn` from backend/ and `pytest` from the
# repo root both find the same file.
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        # Real environment variables win over .env, which is what lets Docker
        # and CI inject config without mounting a file.
        # `extra="ignore"` keeps an unrelated variable in the shell (PATH,
        # PYTHONPATH, CI runner noise) from failing app startup.
        extra="ignore",
        case_sensitive=False,
    )

    # --- app -----------------------------------------------------------
    app_name: str = "FastAPI Starter"
    log_level: str = "INFO"
    sql_echo: bool = False

    # --- database ------------------------------------------------------
    # No default. A missing DATABASE_URL should stop the process at import
    # time with a clear pydantic error, not surface as a connection failure
    # on the first request.
    database_url: str
    test_database_url: str = ""

    # --- auth ----------------------------------------------------------
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- cors ----------------------------------------------------------
    # Typed as a plain string because pydantic-settings parses a `list[str]`
    # field as JSON, which would force `["http://a","http://b"]` quoting into
    # .env. Comma-separated is what everyone expects; `cors_origin_list` splits.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Add your own domain-specific settings here as the app grows — this is
    # the ONE place a tunable constant belongs, never scattered inline at a
    # call site. (The RAG starter this template was extracted from adds an
    # --- openai --- and --- rag tuning --- block right here, for example.)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached so .env is read once per process rather than per dependency call.

    Also makes Settings a stable singleton, so overriding it in tests overrides
    it everywhere.
    """
    return Settings()

"""
C-IAW Backend Configuration
Loads all environment variables from the single root .env file.
Resolves:  career-agent/.env  (two levels up from this file)
Fallback:  career-agent/backend/.env  (kept for backward compat)

Priority: .env FILE > system env vars (prevents stale cached keys).
"""
from pathlib import Path
from typing import Optional, Tuple, Type, Any
from pydantic_settings import (
    BaseSettings, SettingsConfigDict,
    PydanticBaseSettingsSource, DotEnvSettingsSource, EnvSettingsSource,
)
from pydantic import Field

# ── Resolve root .env path ────────────────────────────────────
_HERE     = Path(__file__).resolve().parent          # backend/app/
_ROOT_ENV = _HERE.parent.parent / ".env"             # career-agent/.env
_LOCAL_ENV = _HERE.parent / ".env"                   # career-agent/backend/.env
_ENV_FILE  = str(_ROOT_ENV) if _ROOT_ENV.exists() else str(_LOCAL_ENV)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # ── Gemini ────────────────────────────────────────────────
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model:   str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")

    # ── Firebase ──────────────────────────────────────────────
    firebase_service_account_path: str = Field(
        default="./firebase-service-account.json",
        alias="FIREBASE_SERVICE_ACCOUNT_PATH",
    )
    firebase_storage_bucket: str = Field(
        default="",
        alias="FIREBASE_STORAGE_BUCKET",
    )

    # ── App ───────────────────────────────────────────────────
    env:             str   = Field(default="development", alias="ENV")
    match_threshold: float = Field(default=92.0,          alias="MATCH_THRESHOLD")
    cors_origins:    str   = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    port:            int   = Field(default=8000,          alias="PORT")

    # ── Single User ───────────────────────────────────────────
    user_id: str = Field(default="local_user", alias="USER_ID")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        **kwargs: Any,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # .env FILE takes priority over system env vars
        # This prevents stale Windows environment variables overriding the file.
        return (init_settings, dotenv_settings, env_settings)

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()

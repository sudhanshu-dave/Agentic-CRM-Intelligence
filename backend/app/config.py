from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_PATH = BACKEND_DIR / "agentic_crm.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


class Settings(BaseSettings):
    APP_NAME: str = "Agentic CRM Intelligence Platform"
    APP_ENV: str = "development"
    DATABASE_URL: str = DEFAULT_DATABASE_URL
    CORS_ORIGINS: str = "http://localhost:5173"

    ENABLE_LLM_CLASSIFICATION: bool = True
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
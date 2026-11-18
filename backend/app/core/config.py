from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables / backend/.env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Insurance Chat API"
    debug: bool = False
    # JSON list in env, e.g. CORS_ORIGINS='["http://localhost:5173"]'
    cors_origins: list[str] = []


settings = Settings()

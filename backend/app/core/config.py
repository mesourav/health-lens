from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """App settings, read from environment variables / backend/.env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Health Lens API"
    debug: bool = False
    # JSON list in env, e.g. CORS_ORIGINS='["http://localhost:5173"]'
    cors_origins: list[str] = []

    # Signs the session cookie. MUST be overridden outside local dev.
    session_secret: str = "dev-only-change-me"
    # Cloud Run serves HTTPS, so cookies should be Secure there.
    session_https_only: bool = False

    # --- Our own AI model (Ollama). Locally: http://localhost:11434 ---
    ollama_url: str = "http://localhost:11434"
    chat_model: str = "gemma3:4b"
    embed_model: str = "nomic-embed-text"
    llm_timeout_s: float = 60.0
    # On Cloud Run, the Ollama service is private; send a Google ID token to call it.
    ollama_use_id_token: bool = False

    # --- Data (prototype: fake JSON + markdown docs) ---
    data_dir: Path = BACKEND_DIR / "data"
    # Built frontend to serve at "/" (set in the Docker image). Empty = don't serve.
    static_dir: Path | None = None


settings = Settings()

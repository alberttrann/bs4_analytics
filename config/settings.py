"""
config/settings.py
Pydantic BaseSettings - reads from environment variables or .env file.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # FastAPI server
    api_host: str  = "0.0.0.0"
    api_port: int  = 8000
    log_level: str = "INFO"

    # Streamlit → API URL
    api_base_url: str = "http://localhost:8000"

    # Pipeline behaviour
    skip_fetch: bool = False   # reuse cached HTML in dev mode
    http_timeout: int = 20

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        case_sensitive    = False


settings = Settings()

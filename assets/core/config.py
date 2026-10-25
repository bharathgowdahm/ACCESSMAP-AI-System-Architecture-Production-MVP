"""Centralized environment configuration via Pydantic v2."""
from functools import lru_cache
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ACCESSMAP AI"
    APP_TAGLINE: str = "Every Route. Every Ability. Equal Freedom."
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./accessmap.db"
    GEMINI_API_KEY: str | None = None
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    MAX_IMAGE_SIZE_MB: int = 5
    DEFAULT_ROUTING_RADIUS_M: int = 1500
    NOMINATIM_USER_AGENT: str = "AccessMapAI-OpenSourcePlatform/1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    # Check for Streamlit secrets compatibility first
    db_url = os.environ.get("DATABASE_URL")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "DATABASE_URL" in st.secrets:
                db_url = st.secrets["DATABASE_URL"]
            if "GEMINI_API_KEY" in st.secrets:
                gemini_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return Settings(
        DATABASE_URL=db_url or "sqlite:///./accessmap.db",
        GEMINI_API_KEY=gemini_key
    )

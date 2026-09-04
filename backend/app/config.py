"""Application configuration."""
from __future__ import annotations

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API
    app_name: str = "Urban Flood Nowcasting System"
    debug: bool = False

    # Rainfall adapter
    open_meteo_timeout: float = 10.0
    open_meteo_cache_ttl_minutes: int = 30
    mumbai_lat: float = 19.0760
    mumbai_lon: float = 72.8777

    # Database (for future use)
    database_url: str = "sqlite:///./flood_nowcast.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
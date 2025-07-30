"""
Application configuration using Pydantic Settings
"""
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    url: str = Field(
        default="sqlite:///light_novels.db",
        description="Database URL for SQLAlchemy connection"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging"
    )
    pool_size: int = Field(
        default=10,
        description="Database connection pool size"
    )
    max_overflow: int = Field(
        default=20,
        description="Maximum overflow connections"
    )

    model_config = {"env_prefix": "DATABASE_"}


class CORSSettings(BaseSettings):
    """CORS configuration settings"""
    origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    methods: List[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed CORS methods"
    )
    headers: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )

    model_config = {"env_prefix": "CORS_"}


class ScraperSettings(BaseSettings):
    """Web scraper configuration settings"""
    delay: int = Field(
        default=6,
        ge=1,
        le=30,
        description="Delay in seconds between scraper requests"
    )
    timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Request timeout in seconds"
    )
    user_agent: str = Field(
        default="Light Novel Bookmarks Bot/1.0.0",
        description="User agent string for scraper requests"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of retry attempts"
    )

    model_config = {"env_prefix": "SCRAPER_"}


class AppSettings(BaseSettings):
    """Main application settings"""
    title: str = Field(
        default="Light Novel Bookmarks API",
        description="Application title"
    )
    description: str = Field(
        default="A personal portal to organize, search, and manage your light novels",
        description="Application description"
    )
    version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)"
    )
    host: str = Field(
        default="127.0.0.1",
        description="Application host"
    )
    port: int = Field(
        default=8000,
        ge=1000,
        le=65535,
        description="Application port"
    )

    model_config = {"env_prefix": "APP_"}


class Settings(BaseSettings):
    """Main settings class that combines all setting groups"""
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    scraper: ScraperSettings = Field(default_factory=ScraperSettings)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


# Global settings instance
settings = Settings() 
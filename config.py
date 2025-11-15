"""Centralized application configuration."""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables."""

    mongodb_uri: str = "mongodb://localhost:27017"
    database_prefix: str = "etl_"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        env_prefix = "ETL_"


def get_settings() -> Settings:
    """Provide a cached settings instance."""

    return Settings()

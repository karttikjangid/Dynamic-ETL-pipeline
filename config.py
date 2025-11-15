"""Centralized application configuration."""


from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv(Path(__file__).resolve().with_name(".env"))



class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables."""

    mongodb_uri: str = "mongodb://localhost:27017"
    database_prefix: str = "etl_"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = SettingsConfigDict(env_prefix="ETL_")


def get_settings() -> Settings:
    """Provide a cached settings instance."""

    return Settings()

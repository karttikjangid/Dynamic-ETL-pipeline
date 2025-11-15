"""Centralized application configuration."""


import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().with_name(".env")
load_dotenv(ENV_FILE)


def _load_mongo_uri_from_env() -> str:
    value = os.getenv("ETL_MONGODB_URI")
    if not value:
        raise ValueError(
            "ETL_MONGODB_URI is not set. Define it in your .env file before running the pipeline."
        )
    return value


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables."""

    mongodb_uri: str = Field(default_factory=_load_mongo_uri_from_env)
    database_prefix: str = "etl_"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_prefix="ETL_",
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Provide a cached settings instance."""

    return Settings()

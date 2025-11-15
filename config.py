"""Centralized application configuration."""


import os
from functools import lru_cache
from pathlib import Path

import spacy
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from spacy.cli.download import download as spacy_download
from spacy.util import is_package


ENV_FILE = Path(__file__).resolve().with_name(".env")
SPACY_MODEL_NAME = "en_core_web_sm"
load_dotenv(ENV_FILE)


def _ensure_spacy_model_installed(model_name: str) -> None:
    """Ensure the required spaCy model exists locally, downloading if needed."""

    if is_package(model_name):
        return

    try:
        spacy.load(model_name)
        return
    except OSError:
        pass

    try:
        spacy_download(model_name)
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        raise RuntimeError(
            f"Failed to download spaCy model '{model_name}'. "
            f"Please run: python -m spacy download {model_name}"
        ) from exc

    try:
        spacy.load(model_name)
    except OSError as exc:  # pragma: no cover - should not happen, but guard anyway
        raise RuntimeError(
            f"spaCy model '{model_name}' is still unavailable after download."
        ) from exc


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
    mongodb_database: str = "etl_db"  # Single fixed database for entire ETL pipeline
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

    _ensure_spacy_model_installed(SPACY_MODEL_NAME)
    return Settings()

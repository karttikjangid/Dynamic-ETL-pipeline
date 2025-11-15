"""API middleware configuration."""

from __future__ import annotations

from fastapi import FastAPI


def register_middleware(app: FastAPI) -> None:
    """Register global middleware on the FastAPI app."""

    raise NotImplementedError

"""API middleware configuration."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


def register_middleware(app: FastAPI) -> None:
    """Register global middleware on the FastAPI app."""

    settings = get_settings()

    # CORS configuration: allow configurable origins (default to wildcard for dev).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = f"{duration_ms:.2f}"
        logger.info(
            "%s %s completed in %.2f ms - status=%s req_id=%s",
            request.method,
            request.url.path,
            duration_ms,
            response.status_code,
            request_id,
        )
        return response


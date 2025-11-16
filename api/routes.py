"""API routes and application factory."""

from __future__ import annotations

from fastapi import APIRouter, Body, FastAPI, File, Form, Query, UploadFile

from .handlers import (
    handle_get_records,
    handle_get_schema,
    handle_get_schema_history,
    handle_health_check,
    handle_query_execution,
    handle_upload,
)
from .middleware import register_middleware
from .validators import validate_query_payload, validate_upload_payload


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title="Dynamic ETL Pipeline", version="1.0.0")
    register_middleware(app)
    app.include_router(_build_router())
    return app


def _build_router() -> APIRouter:
    router = APIRouter()

    @router.post("/upload")
    async def upload_endpoint(
        file: UploadFile = File(...),
        source_id: str | None = Form(None),
        version: int | None = Form(None),
    ):
        normalized_payload = validate_upload_payload(file, source_id, version)
        return await handle_upload(file, normalized_payload["source_id"], normalized_payload["version"])

    @router.get("/schema")
    async def schema_endpoint(source_id: str = Query(...)):
        return await handle_get_schema(source_id)

    @router.get("/schema/history")
    async def schema_history_endpoint(source_id: str = Query(...)):
        return await handle_get_schema_history(source_id)

    @router.get("/records")
    async def records_endpoint(
        source_id: str = Query(...),
        query_id: str | None = Query(None),
        limit: int = Query(100, ge=1, le=1000),
    ):
        return await handle_get_records(source_id, limit, query_id)

    @router.post("/query")
    async def query_endpoint(source_id: str = Query(...), query: dict = Body(...)):
        validate_query_payload(query)
        return await handle_query_execution(source_id, query)

    @router.get("/health")
    async def health_endpoint():
        return await handle_health_check()

    return router

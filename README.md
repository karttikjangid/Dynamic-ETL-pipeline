# Dynamic ETL Pipeline

Tier-A ETL pipeline skeleton for deterministic ingestion of JSON and key-value fragments from `.txt` and `.md` files. The project is organized according to the provided architectural guidelines and is ready for incremental implementation of each module.

## Features

- Strict module boundaries (extractors, normalizers, inference, storage, services, API, core, utils)
- Deterministic schema evolution scaffolding
- MongoDB-first storage abstractions
- Placeholder services and API routes for uploads, schema inspection, querying, and health checks

## Getting Started

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables by copying `.env.example` to `.env` and updating the values.

4. Run the API once implemented:

```bash
uvicorn main:main --reload
```

## Next Steps

- Implement extractor logic for JSON and key-value fragments
- Build normalizers that clean and standardize extracted data
- Add schema inference leveraging pandas/pyarrow
- Connect storage layer to a running MongoDB instance
- Flesh out services and API handlers with actual business logic

## API Overview

| Endpoint | Method | Description |
| --- | --- | --- |
| `/upload` | `POST` | Multipart upload accepting `.txt`/`.md` files plus optional `source_id` and `version`. Returns `UploadResponse` including fragment summary and schema identifiers. |
| `/schema` | `GET` | Requires `source_id`. Returns the most recent schema metadata along with compatible databases. |
| `/schema/history` | `GET` | Requires `source_id`. Returns historical schemas and diffs for deterministic evolution tracking. |
| `/query` | `POST` | Execute strict Mongo-like dict queries for a given `source_id`. Responds with `query_id` for later retrieval. |
| `/records` | `GET` | Requires `source_id` and `query_id`. Fetches cached query results (supports pagination via `limit`). |
| `/health` | `GET` | Lightweight health probe reporting pipeline/storage readiness. |

### Upload Example

```bash
curl -X POST \
	-F "file=@sample.md" \
	-F "source_id=demo_notes" \
	http://localhost:8000/upload
```

### Query Execution Example

```bash
curl -X POST "http://localhost:8000/query?source_id=demo_notes" \
	-H "Content-Type: application/json" \
	-d '{"field": {"$eq": 42}}'
```

Use the returned `query_id` to fetch results:

```bash
curl "http://localhost:8000/records?source_id=demo_notes&query_id=<id>&limit=50"
```

# Dynamic ETL Pipeline

Modular Tier-A pipeline for deterministic ingestion of JSON blobs, key–value sections, and Markdown code blocks sourced from `.txt` and `.md` files. The system extracts structured fragments, normalizes them through shared Pydantic models, infers and versions schemas, persists into MongoDB, and exposes strict query endpoints via FastAPI.

## Highlights

- **Deterministic schema evolution** – schema versions only increment when the inferred field set changes; IDs follow `schema_id = {source_id}_v{version}`.
- **Tightly scoped modules** – extractors, normalizers, inference, storage, services, API, core, and utils each own a single concern with enforced dependency rules.
- **Mongo-first storage abstractions** – schema-aware collection creation, validation rules, and insert/query helpers.
- **Strict queries only** – services and API accept explicit Mongo/SQL-like dict payloads (no natural language interpretation).

## Pipeline Flow

```
File ingest (.txt/.md)
	↓ parse via `extractors/file_parser.py`
Extraction (JSON + KV)
	↓ produces `ExtractedRecord`
Normalization per source type
	↓ yields `NormalizedRecord`
Schema detection + scoring (pandas + PyArrow)
	↓ `SchemaMetadata` persisted + diffed
MongoDB storage + query services
	↓ FastAPI routes for upload/schema/query/records/health
```

## Module Boundaries & Allowed Dependencies

| Module | Responsibility | Can depend on |
| --- | --- | --- |
| `core/` | Shared Pydantic models, constants, exceptions | — (available everywhere) |
| `utils/` | Logging, validation, file helpers | — |
| `extractors/` | Parse files, pull JSON/KV fragments | `core`, `utils` |
| `normalizers/` | Clean + standardize extracted data | `core`, `utils` |
| `inference/` | Schema detection, type mapping, scoring | `core`, `utils` |
| `storage/` | Mongo connection, schema store, migrations | `core`, `utils` |
| `services/` | Orchestrate pipeline, schemas, queries | `core`, `utils`, extractors/normalizers/inference/storage |
| `api/` | FastAPI routes, validation, middleware | `services`, `core`, `utils` |

> Dependency rule of thumb: `main.py → api → services → (extractors | normalizers | inference | storage)`; reverse edges are prohibited.

## Repository Map

- `config.py` – settings bootstrap (dotenv + Pydantic).
- `main.py` – FastAPI application factory entry point.
- `core/models.py` – canonical data contracts (`ExtractedRecord`, `SchemaMetadata`, `UploadResponse`, etc.).
- `extractors/` – file parsing utilities plus JSON & KV extractors, orchestrator, and stats logging.
- `normalizers/` – JSON/KV normalizers and orchestration helpers that emit normalized dicts.
- `inference/` – schema detector (pandas ➜ PyArrow), type mapper, confidence scoring, schema generator.
- `storage/` – Mongo connection singleton, collection/schema managers, migration helpers, CRUD abstractions.
- `services/` – pipeline, schema, query, and orchestrator services coordinating cross-module work.
- `api/` – FastAPI routes, validators, middleware, and async handlers invoking services.
- `docs/` – deep dives (extractor implementations, normalization guide, schema diffing, orchestration, visual guide).
- `tests/` – smoke tests for extractors plus end-to-end service scaffolding.

## Getting Started

### Prerequisites

- Python 3.11+ (project tested on Linux; commands below use `fish`).
- Local MongoDB instance or connection string available via `.env` (development may leverage `mongomock`).

### Setup

1. Create and activate a virtual environment:

	```bash
	python -m venv .venv
	source .venv/bin/activate
	```

2. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

3. Download spaCy language model:

	```bash
	python -m spacy download en_core_web_sm
	```

4. Configure environment variables:

	```bash
	cp .env.example .env
	# update Mongo URI, database names, logging level, etc.
	```

5. Launch the API with auto-reload for local development:

	```bash
	uvicorn main:main --reload
	```

### Testing

Lightweight smoke suites live under `tests/`. Run them with:

```bash
pytest
```

## Working with the Pipeline

1. **Upload** a `.txt`/`.md` file via `/upload`. The handler streams the file through the extractor orchestrator, returning `UploadResponse` with `parsed_fragments_summary = {"json_fragments": X, "kv_pairs": Y}` and extracted counts.
2. **Normalization** is type-aware: JSON fragments pass through `JSONNormalizer`, KV fragments through `KVNormalizer`, each producing `NormalizedRecord` instances with source provenance and extraction confidence.
3. **Schema Generation** leverages pandas + PyArrow to infer field types, map them via `inference/type_mapper.py`, compute confidence scores, and persist the resulting `SchemaMetadata` and diffs.
4. **Storage & Querying** rely on MongoDB collections built from schema validation docs. Strict query payloads (dict form) are required for `/query`; results are fetched via `/records` with pagination-capable limits.

Re-uploading identical content is idempotent: schema versions are reused, and migration helpers in `storage/migration.py` only trigger when `SchemaDiff` detects real changes.

## API Surface

| Endpoint | Method | Description |
| --- | --- | --- |
| `/upload` | `POST` | Multipart upload (`file`, optional `source_id`, optional `version`). Returns `UploadResponse` containing schema IDs and fragment summary. |
| `/schema` | `GET` | Fetch the current `SchemaMetadata` for a `source_id`. |
| `/schema/history` | `GET` | Retrieve historical schemas plus computed diffs for deterministic evolution tracking. |
| `/query` | `POST` | Execute a strict Mongo-like dict query for a source; returns `QueryResult` with execution metadata. |
| `/records` | `GET` | Pull materialized query results (requires `source_id`, optional `query_id`, `limit`). |
| `/health` | `GET` | Lightweight readiness probe for API + storage connectivity. |

### Upload Example

```bash
curl -X POST \
	 -F "file=@sample.md" \
	 -F "source_id=demo_notes" \
	 http://localhost:8000/upload
```

### Query Example

```bash
curl -X POST "http://localhost:8000/query?source_id=demo_notes" \
	 -H "Content-Type: application/json" \
	 -d '{"field": {"$eq": 42}}'
```

Use the returned `query_id` (if provided) to fetch records:

```bash
curl "http://localhost:8000/records?source_id=demo_notes&query_id=<id>&limit=50"
```

## Documentation & References

- `guidelines.md` – authoritative architecture, dependency rules, and scope.
- `docs/EXTRACTOR_*`, `docs/NORMALIZER_*`, `docs/ORCHESTRATOR_IMPLEMENTATION.md` – module-specific implementation notes.
- `docs/COMPUTE_SCHEMA_DIFF.md`, `docs/VISUAL_OUTPUT_GUIDE.md` – schema evolution and visualization references.

Refer to these documents when fleshing out modules to keep the pipeline deterministic and Tier-A compliant.

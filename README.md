# Dynamic ETL Pipeline

Modular Tier-A pipeline for deterministic ingestion of JSON blobs, key–value sections, and Markdown code blocks sourced from `.txt` and `.md` files. The system extracts structured fragments, normalizes them through shared Pydantic models, infers and versions schemas, persists into MongoDB and SQLite, and exposes strict query endpoints via FastAPI.

## Highlights

- **Intelligent Schema Versioning** – Versions increment only when schema structure changes (field additions/removals/types/nullability); duplicate uploads reuse existing versions via signature comparison.
- **Hybrid Multi-Backend Storage** – Automatic routing between MongoDB (nested/complex data) and SQLite (tabular data) based on source type and data structure.
- **Deterministic Schema Evolution** – Schema versions only increment when the inferred field set changes; IDs follow `schema_id = {source_id}_v{version}`.
- **Tightly scoped modules** – extractors, normalizers, inference, storage, services, API, core, and utils each own a single concern with enforced dependency rules.
- **Schema-aware storage abstractions** – Dynamic collection/table creation, validation rules, and insert/query helpers for both MongoDB and SQLite.
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
Duplicate detection via signature comparison
	↓ Version reuse or increment
Hybrid storage routing (MongoDB vs SQLite)
	↓ Schema-aware collection/table creation
MongoDB storage (nested/complex data) + SQLite storage (tabular data)
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

## Storage Strategy

The pipeline employs a **hybrid multi-backend approach** with intelligent data routing:

### Storage Backends

| Backend | Purpose | Data Types | Schema Handling | Versioning |
|---------|---------|------------|-----------------|------------|
| **MongoDB** | Complex/nested data | `json`, `yaml_block` | JSON Schema validation | Schema-level versioning |
| **SQLite** | Tabular/structured data | `html_table`, `csv_block`, `kv` | Relational tables | Table-level versioning |

### Data Routing Criteria

1. **Primary**: Source type classification
   - `json`, `yaml_block` → MongoDB (preserves nesting)
   - `html_table`, `csv_block`, `kv` → SQLite (relational optimization)

2. **Secondary**: Data structure flatness
   - Flat schemas (no `object`/`array` types) → SQLite compatible
   - Complex schemas → MongoDB required

### Versioning Mechanism

**Schema signatures** determine version changes, not upload frequency:

- **Tier-B (Advanced)**: Genson-based structural hashing
- **Tier-A (Fallback)**: Field tuple comparison `(name, type, nullable)`
- **Duplicate Detection**: Identical signatures reuse existing versions
- **Change Triggers**: Field additions/removals, type changes, nullability shifts

### Storage Locations

- **MongoDB**: Collections named `{source_id}_records`
- **SQLite**: Single database file `./data/sqlite/etl_pipeline.db` with versioned tables `{source_id}_v{version}`

## Repository Map

- `config.py` – settings bootstrap (dotenv + Pydantic).
- `main.py` – FastAPI application factory entry point.
- `core/models.py` – canonical data contracts (`ExtractedRecord`, `SchemaMetadata`, `UploadResponse`, etc.).
- `extractors/` – file parsing utilities plus JSON & KV extractors, orchestrator, and stats logging.
- `normalizers/` – JSON/KV normalizers and orchestration helpers that emit normalized dicts.
- `inference/` – schema detector (pandas ➜ PyArrow), type mapper, confidence scoring, schema generator.
- `storage/` – MongoDB connection singleton, SQLite connection manager, schema store, collection/table managers, migration helpers, CRUD abstractions for both backends.
- `services/` – pipeline, schema, query, and orchestrator services coordinating cross-module work.
- `api/` – FastAPI routes, validators, middleware, and async handlers invoking services.
- `docs/` – deep dives (extractor implementations, normalization guide, schema diffing, orchestration, visual guide).
- `tests/` – smoke tests for extractors plus end-to-end service scaffolding.

## Getting Started

### Prerequisites

- Python 3.11+ (project tested on Linux; commands below use `fish`).
- Local MongoDB instance or connection string available via `.env` (development may leverage `mongomock`).
- SQLite (automatically managed - creates `./data/sqlite/etl_pipeline.db`).

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
4. **Duplicate Detection** compares schema signatures (Genson-based or field-based) to determine if content is identical; matching signatures reuse existing schema versions.
5. **Hybrid Storage Routing** automatically categorizes data by source type and structure:
   - Complex/nested data (`json`, `yaml_block`) → MongoDB collections
   - Tabular data (`html_table`, `csv_block`, `kv`) → SQLite tables
6. **Storage & Querying** rely on backend-specific schema validation. Strict query payloads (dict form) are required for `/query`; results are fetched via `/records` with pagination-capable limits.

Re-uploading identical content is idempotent: schema versions are reused, and migration helpers in `storage/migration.py` only trigger when `SchemaDiff` detects real structural changes.

## Design Decisions & Workflow

### Why Hybrid Storage?
- **Performance Optimization**: Tabular data performs better in relational databases (SQLite) with structured queries and aggregations
- **Flexibility**: Complex nested data requires document storage (MongoDB) to preserve structure
- **Automatic Routing**: Source type + data structure analysis ensures optimal backend selection
- **Cost Efficiency**: Single SQLite file vs MongoDB deployment complexity

### Why Intelligent Versioning?
- **Deterministic Evolution**: Versions only increment on actual schema changes, not uploads
- **Storage Efficiency**: Identical schemas reuse versions, preventing redundant storage
- **Backward Compatibility**: Signature-based comparison handles schema evolution gracefully
- **Audit Trail**: Version history tracks meaningful structural changes over time

### Workflow Philosophy
1. **Extract First**: Parse raw files into structured fragments
2. **Normalize Second**: Standardize data formats and types
3. **Infer Third**: Generate schemas from actual data patterns
4. **Compare Fourth**: Check for structural changes before versioning
5. **Route Fifth**: Choose optimal storage backend
6. **Store Sixth**: Persist with schema validation and indexing

This approach ensures **data integrity**, **performance optimization**, and **deterministic behavior** while handling diverse data sources.

## TODO

- [ ] **Add storage for raw text and HTML files** (except tables) - currently only structured fragments are stored; implement raw content preservation for full fidelity
- [ ] Expand Tier-B features (enhanced diffing, migration tracking)
- [ ] Add data export capabilities
- [ ] Implement advanced query builders

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
- `storage/` – hybrid storage implementation details (MongoDB + SQLite routing, versioning strategies).
- `inference/genson_integration.py` – advanced schema signature computation for versioning.

Refer to these documents when fleshing out modules to keep the pipeline deterministic and maintain the hybrid storage approach.

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

> **📖 For detailed workflow information including all custom class objects, data transformations, and technical specifications, see [`docs/workflow.md`](docs/workflow.md).**

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

| Backend | Purpose | Data Types | Schema Handling | Versioning | Location |
|---------|---------|------------|-----------------|------------|----------|
| **MongoDB** | Complex/nested data | `json`, `yaml_block` | JSON Schema validation | Schema-level versioning | Collections: `{source_id}_records` |
| **SQLite** | Tabular/structured data | `html_table`, `csv_block`, `kv` | Relational tables | Table-level versioning | Tables: `{source_id}_v{version}` |

### Data Routing Criteria

1. **Primary**: Source type classification
   - `json`, `yaml_block` → MongoDB (preserves nesting)
   - `html_table`, `csv_block`, `kv` → SQLite (relational optimization)

2. **Secondary**: Data structure flatness
   - Flat schemas (no `object`/`array` types) → SQLite compatible
   - Complex schemas → MongoDB required

### Storage Implementation Details

#### MongoDB Collections
- **Naming**: `{source_id}_records` (e.g., `user_data_records`)
- **Validation**: JSON Schema with `bsonType` constraints
- **Indexing**: Automatic indexes on all schema fields
- **Data**: Native BSON documents preserving full structure

#### SQLite Tables
- **Naming**: `{source_id}_v{version}` (e.g., `user_data_v1`)
- **Structure**: Dynamic table creation with typed columns
- **Flattening**: Nested objects flattened with underscore separators
- **Location**: `./data/sqlite/etl_pipeline.db`

### Schema Compatibility Determination
```python
def get_compatible_dbs_for_schema(schema: SchemaMetadata) -> List[str]:
    # Check if schema is "flat" enough for SQLite
    is_flat = all(field.type not in ["object", "array"] for field in schema.fields)
    
    compatible = []
    if is_flat:
        compatible.append("sqlite")  # Can use relational storage
    compatible.append("mongodb")     # MongoDB can handle anything
    
    return compatible
```

### Versioning Mechanism

**Schema signatures** determine version changes, not upload frequency:

- **Genson-based structural hashing**
- **Duplicate Detection**: Identical signatures reuse existing versions
- **Change Triggers**: Field additions/removals, type changes, nullability shifts

```python
# Version increment logic
target_version = 1
duplicate_upload = False
if existing_schema is not None:
    duplicate_upload = handle_duplicate_upload(source_id, new_schema, existing_schema)
    target_version = existing_schema.version if duplicate_upload else existing_schema.version + 1
```

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

### Why Dual Schema Generation?
The pipeline uses **both custom inference AND Genson** for complementary purposes:

#### Custom Inference (Primary)
- **Purpose**: Fast, ETL-optimized schema for pipeline operations
- **Output**: `SchemaField[]` with confidence scores, examples, metadata
- **Performance**: Lightweight, custom logic for ETL edge cases
- **Use Case**: Core pipeline operations, validation, storage

#### Genson Schema (Secondary)
- **Purpose**: Advanced schema comparison for versioning
- **Output**: Standard JSON Schema format
- **Features**: Structural signatures, deep diffing capabilities
- **Use Case**: Duplicate detection, schema evolution tracking

### Workflow Philosophy
1. **Extract First**: Parse raw files into structured fragments
2. **Normalize Second**: Standardize data formats and types
3. **Compare Third**: Check for structural changes before versioning
4. **Infer Fourth**: Generate schemas from actual data patterns
5. **Route Fifth**: Choose optimal storage backend
6. **Store Sixth**: Persist with schema validation and indexing

This approach ensures **data integrity**, **performance optimization**, and **deterministic behavior** while handling diverse data sources.

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

## Schema Generation & Versioning

The pipeline employs a **dual-schema architecture** for optimal performance and intelligent versioning:

### Primary Schema System (Custom Inference)
**Purpose:** Fast, ETL-optimized schema generation for pipeline operations

```python
# Core type detection
field_types = detect_data_types(records)  # Maps field → type
schema_fields = build_schema_fields(records, field_types, field_confidences)
```

**Features:**
- **Simple type system**: `string`, `integer`, `number`, `boolean`, `object`, `array`, `null`
- **Rich metadata**: Confidence scores, nullability detection, example values
- **Performance**: Lightweight inference using `infer_type()` + `merge_types()`
- **Control**: Custom logic handles ETL-specific edge cases

### Secondary Schema System (Genson)
**Purpose:** Advanced schema comparison for intelligent versioning

```python
# Signature generation for versioning
genson_schema = generate_genson_schema(records)  # JSON Schema format
signature = compute_schema_signature(genson_schema)  # Hash for comparison
```

**Features:**
- **Standard JSON Schema**: Full JSON Schema specification compliance
- **Structural signatures**: Deterministic hashing for duplicate detection
- **Deep comparison**: Enables sophisticated schema evolution tracking
- **Interoperability**: Standard format for external tools

### Versioning Logic
**Schema versions increment only on structural changes:**

1. **Signature Comparison**: Genson-based structural hashing
2. **Duplicate Detection**: Identical signatures reuse existing versions
3. **Change Triggers**: Field additions/removals, type changes, nullability shifts

```python
# Version increment logic
if existing_schema:
    duplicate = handle_duplicate_upload(source_id, new_schema, existing_schema)
    target_version = existing_schema.version if duplicate else existing_schema.version + 1
```

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

### Query Examples

#### MongoDB engine (default)

```bash
curl -X POST "http://localhost:8000/query?source_id=demo_notes" \
	 -H "Content-Type: application/json" \
	 -d '{
	   "filter": {"field": {"$eq": 42}},
	   "limit": 25
	 }'
```

#### SQLite engine

Structured/tabular sources (CSV, HTML tables, KV blocks) can be queried via SQLite by setting `engine` to `"sqlite"` and providing SQL-inspired clauses:

```bash
curl -X POST "http://localhost:8000/query?source_id=demo_tables" \
	 -H "Content-Type: application/json" \
	 -d '{
	   "engine": "sqlite",
	   "select": ["account_id", "branch_code", "balance", "status"],
	   "where": {
	     "status": "active",
	     "balance": {"$gt": 9000}
	   },
	   "order_by": [["balance", "desc"]],
	   "limit": 10
	 }'
```

Supported SQLite clauses:

- `select`: list of column names (defaults to `*`).
- `where`: dict of column ➜ value / operator maps supporting `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, and `$like`.
- `order_by`: list of `[column, direction]` or `{column: direction}` entries where direction may be `asc`, `desc`, `1`, or `-1`.
- `limit`: positive integer (defaults to 100, capped at 1000).

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

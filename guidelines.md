# **`guidelines.md` — Dynamic ETL Pipeline (Tier-A and Tier-B)**

### **Version: 2.0 — Tier‑B Ready, with SQLite, NER, DeepDiff, and Genson Versioning**

### **Scope: `.txt` / `.md` ingestion → JSON, KV, HTML, CSV, YAML extraction → normalization → schema inference → MongoDB/SQLite storage → strict query execution (+ optional NER enrichment)**

---

## 1️⃣ Mission & non-goals

Build a **deterministic, schema‑evolving ETL pipeline** for unstructured data spanning **Tier‑A and Tier‑B** complexity:

* Tier‑A: JSON, KV, Markdown.
* Tier‑B: messy mixed content (HTML snippets, CSV‑like fragments, partial structures, semi‑structured sections).

The system must automatically ingest → extract → normalize → infer schema → version using **DeepDiff + Genson** → store records in **MongoDB** (complex) or **SQLite** (tabular) → run strict DB queries.

**Goals:** reliability, determinism, incremental schema evolution, transparent diffs, strong evidence reporting.

**Non‑goals:** natural‑language queries, PDFs/OCR (Tier‑C), complex distributed storage.

---

## 2️⃣ End-to-end flow (Tier A + Tier B)

1. **FastAPI upload** (`/upload`) accepts `.txt` / `.md`, validates payloads, persists temp files, and delegates to `services.pipeline_service.process_upload`.
2. **Extraction orchestrator** parses the file (`extractors.file_parser`), runs all extractors (JSON, KV, HTML, CSV, YAML), merges deterministic `ExtractedRecord`s, and emits `fragment_stats = {"json_fragments": X, "kv_pairs": Y, "html_tables": Z, "csv_blocks": W, "yaml_blocks": V, "total_records": T}`.
3. **Normalization orchestrator** groups records by `source_type` and routes to appropriate normalizers (JSONNormalizer, KVNormalizer, CSVNormalizer, HTMLTableNormalizer) to build `NormalizedRecord` objects with provenance + confidence metadata.
4. **Schema inference** (`inference.schema_generator`) uses Genson for base JSON-schema aggregation plus custom layer for type-confidence, nullable detection, semantic hints, then returns `SchemaMetadata`.
5. **Schema Versioning** computes signature from Genson canonical schema, compares previous → new via DeepDiff; increments version on structural changes.
6. **Storage routing** (`storage.storage_router`) categorizes records by data shape: complex/nested → MongoDB, tabular → SQLite. Creates/updates validated collections/tables, batches inserts (with schema-aware validation), and persists schema versions + diffs.
7. **Query + records APIs** require structured dict payloads, execute via `services.query_service`, cache results for 10 minutes, and expose `/records` for follow-up retrieval using the issued `query_id`.
8. **Optional NER enrichment** applies spaCy (`services.ner_service`) after normalization; failures are logged but do not break uploads.

---

## 3️⃣ Module boundaries & dependency rules

| Module | Responsibility (implemented artifacts) | Allowed dependencies |
| --- | --- | --- |
| `core/` | Pydantic models (`ExtractedRecord`, `NormalizedRecord`, `SchemaMetadata`, `UploadResponse`, `QueryResult`, etc.), constants & shared exceptions. | _Available to all_ |
| `utils/` | Structured logging (`utils.logger`), filesystem helpers, validation utilities. | _Available to all_ |
| `extractors/` | File parsing, JSON/KV/HTML/CSV/YAML extraction, extraction stats logging. | `core`, `utils` |
| `normalizers/` | Type inference + key standardization for all payload types, orchestrated normalization APIs. | `core`, `utils` |
| `inference/` | Genson + custom schema detection, semantic type mapping, confidence scoring, schema generation/diffs. | `core`, `utils` |
| `storage/` | MongoDB/SQLite connections, schema store, collection/table validation/indexing, document insertion/retrieval, schema migrations. | `core`, `utils` |
| `services/` | Pipeline orchestration, schema lifecycle mgmt, strict query execution, duplicate-upload detection, optional NER. | `core`, `utils`, `extractors`, `normalizers`, `inference`, `storage` |
| `api/` | FastAPI app factory, routes, validators, middleware, query result caching. | `services`, `core`, `utils` |

**Dependency rule recap:** `main.py → api → services → (extractors | normalizers | inference | storage)`. `core/` + `utils/` are leaf-free helpers. No reverse edges (`extractors` must never import `services`, `storage` never imports `extractors`, etc.).

---

## 4️⃣ Core contracts (`core/models.py`)

- **`ExtractedRecord`** — structured output of extractors (`data`, `source_type in {"json","kv","html_table","csv_block","yaml_block"}`, `confidence`).
- **`NormalizedRecord`** — canonical payload emitted by normalizers with provenance + `extraction_confidence`.
- **`SchemaField` / `SchemaMetadata`** — schema definition, compatible DB list (`["mongodb","sqlite"]`), timestamps, record counts, extraction stats.
- **`SchemaDiff`** — added/removed/type-change deltas + migration notes.
- **`UploadResponse`** — canonical upload reply with record counts and `parsed_fragments_summary = {"json_fragments": X, "kv_pairs": Y, "html_tables": Z, "csv_blocks": W, "yaml_blocks": V}`.
- **`GetSchemaResponse` / `GetSchemaHistoryResponse` / `GetRecordsResponse` / `QueryResult`** — service + API response envelopes reused across modules.

---

## 5️⃣ Module deep dive

### 5.1 Extractors (`extractors/`)
- **`file_parser.py`** supports `.txt` & `.md`, with fenced-code-block helpers for Markdown scenarios.
- **`json_extractor.py`** performs brace-stack scanning, attempts multiple JSON parsing strategies (raw, trailing-comma cleanup, quote normalization), and records parse failures with `_parse_error` metadata.
- **`kv_extractor.py`** isolates contiguous `key: value` sections outside JSON regions, standardizes keys, and captures deterministic offsets + chunk IDs.
- **`html_extractor.py`** detects `<table>...</table>` elements, converts to row arrays, attaches `html_table_id` + offsets.
- **`csv_extractor.py`** uses regex-based row alignment, infers headers, converts to records.
- **`yaml_extractor.py`** locates YAML blocks, parses them, attaches offsets.
- **`orchestrator.py`** coordinates all extractors, merges outputs, logs stats through the shared logger, and returns `(List[ExtractedRecord], fragment_stats)` consumed downstream.

### 5.2 Normalizers (`normalizers/`)
- **`JSONNormalizer`** validates dict-shaped payloads, recursively cleans values, and performs lightweight type inference for string scalars.
- **`KVNormalizer`** standardizes keys (lowercase + underscores, special-char stripping) and infers primitive types/ISO date strings while preserving deterministic ordering.
- **`csv_normalizer.py`** and **`html_normalizer.py`** handle tabular data normalization.
- **`orchestrator.py`** groups records by `source_type`, dispatches to the right normalizer, and exposes helper APIs for single-fragment normalization when necessary.

### 5.3 Inference (`inference/`)
- **`schema_detector.py`** uses Genson for base schema aggregation, attaches custom metadata like type-confidence, nullable, semantic hints.
- **`type_mapper.py`** maps types with helpers like `infer_type`, `detect_semantics`, and deterministic union resolution.
- **`confidence_scorer.py`** aggregates coverage/type-consistency metrics into per-field confidence (0.0–1.0).
- **`schema_generator.py`** ties everything together: builds `SchemaField` instances (nullable detection, example values, confidence), computes schema stats, and surfaces diff utilities for downstream migration planning.

### 5.4 Storage (`storage/`)
- **`connection.py`** exposes MongoDB thread-safe singleton (`MongoConnection.get_instance`) based on env-configured URI.
- **`sqlite_connection.py`** handles SQLite connections and table management.
- **`collection_manager.py`** builds MongoDB JSON-schema validators, materializes/updates collections.
- **`sqlite_table_manager.py`** creates SQLite tables per schema version.
- **`document_inserter.py`** and **`sqlite_document_inserter.py`** batch inserts with schema-aware validation.
- **`document_retriever.py`** centralizes paginated reads/count helpers.
- **`schema_store.py`** persists schema versions, exposes history lookups.
- **`migration.py`** compares versions (`SchemaDiff`), applies migrations.
- **`storage_router.py`** decides MongoDB vs SQLite based on data shape.

### 5.5 Services (`services/`)
- **`pipeline_service.process_upload`** orchestrates the full upload lifecycle: extraction → normalization → optional NER → schema inference → dedup/versioning → storage routing → insertion → schema persistence.
  - Combines extractor stats with schema stats so `UploadResponse.parsed_fragments_summary` always reflects all categories.
  - NER enrichment uses `services.ner_service.apply_ner_to_fragments`; failures are logged, not fatal.
- **`schema_service`** exposes `compute_schema_for_source`, `get_current_schema`, `get_schema_history` (with DeepDiff diffs), and `handle_schema_evolution`.
- **`query_service`** enforces dict payloads, caps limits, supports multi-field sort, executes against DB/collection names.
- **`orchestrator.py`** slugifies `source_id`s, detects duplicates via schema signatures.
- **`ner_service.py`** loads spaCy `en_core_web_sm`, attaches entity maps per fragment.

### 5.6 API layer (`api/` + `main.py`)
- **`routes.create_app()`** builds the FastAPI app, registers middleware, wires endpoints.
- **`validators.py`** constrains uploads to `.txt`/`.md`, enforces safe `source_id`s, rejects natural-language queries.
- **`middleware.py`** configures CORS, injects request IDs + response-time headers, logs metrics.
- **`handlers.py`** streams uploads to disk, offloads work to threads, wraps errors, introduces `QueryResultCache` (TTL 600s).
  - `/records` requires `query_id` and serves cached results.
- **`main.py`** is application factory for `uvicorn`.

### 5.7 Utilities & configuration
- **`config.py`** centralizes settings via `pydantic-settings`, auto-loads `.env`, ensures spaCy model.
- **`utils/logger.py`** provides global logger.
- **`utils/file_handler.py`, `utils/helpers.py`, `utils/validators.py`** host reusable helpers.

---

## 6️⃣ Operational policies & guarantees

1. **Deterministic schema versioning** — versions increment on structural changes via DeepDiff; duplicates reuse last schema.
2. **Extraction transparency** — every upload returns `parsed_fragments_summary` with all fragment types.
3. **Strict queries** — API rejects free-form strings; payloads must include `filter`, optional `sort`, `limit`.
4. **Idempotent storage** — validation before insertion; mismatches logged + skipped.
5. **Schema evolution** — migrations apply additive fields and type fallbacks; diffs surfaced via `/schema/history`.
6. **Hybrid storage** — MongoDB for complex, SQLite for tabular; automatic routing.
7. **NER safety** — NER enabled by default but wrapped in try/except; outages never block ingestion.
8. **Observability** — middleware adds `X-Request-ID` + `X-Response-Time-ms`; services log transitions.
9. **Environment parity** — config prefixed with `ETL_` (e.g., `ETL_MONGODB_URI`, `ETL_DATABASE_PREFIX`); host/port configurable.

---

## 7️⃣ API surface (FastAPI)

| Endpoint | Method | Description / Notes |
| --- | --- | --- |
| `/upload` | `POST` | Multipart (`file`, optional `source_id`, optional `version`). Returns `UploadResponse` with schema ID, counts, fragment stats, evidence, and `status ∈ {"success","noop","empty"}`. |
| `/schema` | `GET` | Requires `source_id`; returns latest `SchemaMetadata`. 404 if none exists. |
| `/schema/history` | `GET` | Returns schemas plus DeepDiff diffs. |
| `/query` | `POST` | Body dict with `filter`/`limit`/`sort`. Executes via `services.query_service`, caches results, responds with `QueryResult + query_id`. |
| `/records` | `GET` | Requires `source_id` + `query_id` and optional `limit`. Serves cached results. |
| `/health` | `GET` | Heartbeat with readiness markers. |

All handlers in `api/handlers.py`, validators guard inputs.

---

## 8️⃣ Testing, docs & developer workflow

- **Tests** in `tests/` exercise extractors, normalizers, Tier-A/B pipelines. Run via `pytest`.
- **Documentation** in `docs/` covers implementations, schema diff, etc.
- **Setup**: Python 3.11+, create `.venv`, install `requirements.txt`, download spaCy model, configure `.env`, run `uvicorn main:main --reload`.
- **Databases**: MongoDB via `ETL_MONGODB_URI`, SQLite auto-managed.
- **Linting/style**: `ruff`/`black` friendly.

---

## 9️⃣ Repository map (current)

```
project/
├── main.py
├── config.py
├── requirements.txt
├── guidelines.md  ◀ this document
├── core/
│   ├── constants.py
│   ├── exceptions.py
│   └── models.py
├── extractors/
│   ├── base.py
│   ├── file_parser.py
│   ├── json_extractor.py
│   ├── kv_extractor.py
│   ├── html_extractor.py
│   ├── csv_extractor.py
│   ├── yaml_extractor.py
│   └── orchestrator.py
├── normalizers/
│   ├── base.py
│   ├── json_normalizer.py
│   ├── kv_normalizer.py
│   ├── csv_normalizer.py
│   ├── html_normalizer.py
│   └── orchestrator.py
├── inference/
│   ├── schema_detector.py
│   ├── type_mapper.py
│   ├── confidence_scorer.py
│   ├── schema_generator.py
│   ├── deepdiff_integration.py
│   └── genson_integration.py
├── storage/
│   ├── connection.py
│   ├── sqlite_connection.py
│   ├── collection_manager.py
│   ├── sqlite_table_manager.py
│   ├── document_inserter.py
│   ├── sqlite_document_inserter.py
│   ├── document_retriever.py
│   ├── schema_store.py
│   ├── migration.py
│   └── storage_router.py
├── services/
│   ├── orchestrator.py
│   ├── pipeline_service.py
│   ├── schema_service.py
│   ├── query_service.py
│   └── ner_service.py
├── api/
│   ├── routes.py
│   ├── handlers.py
│   ├── validators.py
│   └── middleware.py
├── utils/
│   ├── file_handler.py
│   ├── helpers.py
│   ├── logger.py
│   └── validators.py
├── docs/
└── tests/
```

Keep contributions aligned with these boundaries and principles to preserve determinism, observability, and Tier-A/B focus.
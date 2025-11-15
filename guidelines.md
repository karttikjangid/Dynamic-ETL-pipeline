# **`guidelines.md` — Dynamic ETL Pipeline (Tier-A scope)**

### **Version: 1.1 — reflects fully implemented stack**

### **Scope: `.txt` / `.md` ingestion → JSON & KV extraction → normalization → schema inference → MongoDB storage → strict query execution (+ optional NER enrichment)**

---

## 1️⃣ Mission & non-goals

- Deliver a **deterministic, schema-evolving ETL pipeline** for well-formed Tier-A inputs (JSON blobs, Markdown code blocks, and key–value sections).
- Guarantee **idempotent re-uploads**: schema versions only increment when the inferred field set changes (`schema_id = f"{source_id}_v{version}"`).
- Provide **strict query APIs** (Mongo-like dict payloads only) and make extraction statistics observable in every upload response.
- Out of scope: HTML/CSV ingestion, malformed payload recovery, natural-language querying, and complex cross-source schema reconciliation.

---

## 2️⃣ End-to-end flow (implemented)

1. **FastAPI upload** (`/upload`) accepts `.txt` / `.md`, validates payloads, persists temp files, and delegates to `services.pipeline_service.process_upload`.
2. **Extraction orchestrator** parses the file (`extractors.file_parser`), runs `JSONExtractor` & `KVExtractor`, merges deterministic `ExtractedRecord`s, and emits `fragment_stats = {"json_fragments": X, "kv_pairs": Y, "total_records": Z}`.
3. **Normalization orchestrator** groups records by `source_type` and routes to `JSONNormalizer` / `KVNormalizer` to build `NormalizedRecord` objects with provenance + confidence metadata.
4. **Schema inference** (`inference.schema_generator`) hydrates pandas → PyArrow, derives field types, confidence scores, and example values, then returns `SchemaMetadata`.
5. **Storage layer** (MongoDB via `storage.connection.MongoConnection`) creates/updates validated collections, batches inserts (with schema-aware validation), and persists schema versions + diffs.
6. **Query + records APIs** require structured dict payloads, execute via `services.query_service`, cache results for 10 minutes, and expose `/records` for follow-up retrieval using the issued `query_id`.
7. **Optional NER enrichment** applies spaCy (`services.ner_service`) after normalization; failures are logged but do not break uploads.

---

## 3️⃣ Module boundaries & dependency rules

| Module | Responsibility (implemented artifacts) | Allowed dependencies |
| --- | --- | --- |
| `core/` | Pydantic models (`ExtractedRecord`, `NormalizedRecord`, `SchemaMetadata`, `UploadResponse`, `QueryResult`, etc.), constants & shared exceptions. | _Available to all_ |
| `utils/` | Structured logging (`utils.logger`), filesystem helpers, validation utilities. | _Available to all_ |
| `extractors/` | File parsing, JSON bracket scanning, KV block detection, extraction stats logging. | `core`, `utils` |
| `normalizers/` | Type inference + key standardization for JSON/KV payloads, orchestrated normalization APIs. | `core`, `utils` |
| `inference/` | pandas/PyArrow schema detection, semantic type mapping, confidence scoring, schema generation/diffs. | `core`, `utils` |
| `storage/` | Mongo connection singleton, schema store, collection validation/indexing, document insertion/retrieval, schema migrations. | `core`, `utils` |
| `services/` | Pipeline orchestration, schema lifecycle mgmt, strict query execution, duplicate-upload detection, optional NER. | `core`, `utils`, `extractors`, `normalizers`, `inference`, `storage` |
| `api/` | FastAPI app factory, routes, validators, middleware, query result caching. | `services`, `core`, `utils` |

**Dependency rule recap:** `main.py → api → services → (extractors | normalizers | inference | storage)`. `core/` + `utils/` are leaf-free helpers. No reverse edges (`extractors` must never import `services`, `storage` never imports `extractors`, etc.).

---

## 4️⃣ Core contracts (`core/models.py`)

- **`ExtractedRecord`** — structured output of extractors (`data`, `source_type in {"json","kv"}`, `confidence`).
- **`NormalizedRecord`** — canonical payload emitted by normalizers with provenance + `extraction_confidence`.
- **`SchemaField` / `SchemaMetadata`** — schema definition, compatible DB list (`["mongodb"]`), timestamps, record counts, extraction stats.
- **`SchemaDiff`** — added/removed/type-change deltas + migration notes.
- **`UploadResponse`** — canonical upload reply with record counts and `parsed_fragments_summary = {"json_fragments": X, "kv_pairs": Y}`.
- **`GetSchemaResponse` / `GetSchemaHistoryResponse` / `GetRecordsResponse` / `QueryResult`** — service + API response envelopes reused across modules.

---

## 5️⃣ Module deep dive

### 5.1 Extractors (`extractors/`)
- **`file_parser.py`** supports `.txt` & `.md`, with fenced-code-block helpers for Markdown scenarios.
- **`json_extractor.py`** performs brace-stack scanning, attempts multiple JSON parsing strategies (raw, trailing-comma cleanup, quote normalization), and records parse failures with `_parse_error` metadata.
- **`kv_extractor.py`** isolates contiguous `key: value` sections outside JSON regions, standardizes keys, and captures deterministic offsets + chunk IDs.
- **`orchestrator.py`** coordinates both extractors, merges outputs, logs stats through the shared logger, and returns `(List[ExtractedRecord], fragment_stats)` consumed downstream.

### 5.2 Normalizers (`normalizers/`)
- **`JSONNormalizer`** validates dict-shaped payloads, recursively cleans values, and performs lightweight type inference for string scalars.
- **`KVNormalizer`** standardizes keys (lowercase + underscores, special-char stripping) and infers primitive types/ISO date strings while preserving deterministic ordering.
- **`orchestrator.py`** groups records by `source_type`, dispatches to the right normalizer, and exposes helper APIs for single-fragment normalization when necessary.

### 5.3 Inference (`inference/`)
- **`schema_detector.py`** hydrates pandas DataFrames, derives PyArrow schemas, walks nested paths, and captures rich statistics (presence counts, numeric ranges, semantic hints, PK/enum suggestions).
- **`type_mapper.py`** maps PyArrow types + semantic detections into application types (`string`, `integer`, `number`, `object`, `array`, etc.) with helpers like `infer_type`, `detect_semantics`, and deterministic union resolution.
- **`confidence_scorer.py`** aggregates coverage/type-consistency metrics into per-field confidence (0.0–1.0).
- **`schema_generator.py`** ties everything together: builds `SchemaField` instances (nullable detection, example values, confidence), computes schema stats, and surfaces diff utilities for downstream migration planning.

### 5.4 Storage (`storage/`)
- **`connection.py`** exposes a thread-safe singleton (`MongoConnection.get_instance`) based on env-configured URI (via `config.get_settings`).
- **`collection_manager.py`** builds Mongo JSON-schema validators, materializes/updates collections, and installs background indexes for known fields.
- **`document_inserter.py`** batches inserts with schema-aware validation (`validate_document_for_insertion`), logging unknown fields/type mismatches.
- **`document_retriever.py`** centralizes paginated reads/count helpers (used by services/tests).
- **`schema_store.py`** persists schema versions (one collection per deployment), exposes history lookups, and ensures deterministic `_id = schema_id`.
- **`migration.py`** compares versions (`SchemaDiff`), applies additive field backfills, and offers best-effort type-migration hooks used by `schema_service.handle_schema_evolution`.

### 5.5 Services (`services/`)
- **`pipeline_service.process_upload`** orchestrates the full upload lifecycle: extraction → normalization → optional NER → schema inference → dedup/versioning (`services.orchestrator.handle_duplicate_upload`) → collection creation → filtered batch insertion → schema persistence.
  - Combines extractor stats with schema stats so `UploadResponse.parsed_fragments_summary` always reflects both categories.
  - NER enrichment uses `services.ner_service.apply_ner_to_fragments`; failures are logged, not fatal.
- **`schema_service`** exposes `compute_schema_for_source` (accepts `NormalizedRecord`s or dicts), `get_current_schema`, `get_schema_history` (with migration diffs), and `handle_schema_evolution` to invoke Mongo migrations when needed.
- **`query_service`** enforces dict payloads, caps limits (default 100, max 1000), supports multi-field sort specs, executes against deterministic DB/collection names, and serializes `ObjectId`s.
- **`orchestrator.py`** slugifies `source_id`s to derive database + collection names (using `ETL_DATABASE_PREFIX`), detects duplicate uploads via schema signatures, and bridges to `schema_store`.
- **`ner_service.py`** loads the spaCy `en_core_web_sm` model at module import, exposes helpers to attach entity maps per fragment, and deduplicates entity values for deterministic output.

### 5.6 API layer (`api/` + `main.py`)
- **`routes.create_app()`** builds the FastAPI app, registers middleware, and wires all endpoints.
- **`validators.py`** constrains uploads to `.txt`/`.md`, enforces safe `source_id`s, and rejects natural-language queries before they reach services.
- **`middleware.py`** configures CORS (dev default `*`), injects per-request IDs + response-time headers, and logs structured request metrics.
- **`handlers.py`** streams uploads to disk, offloads blocking work to threads (`run_in_threadpool`), wraps service errors into HTTP errors, and introduces `QueryResultCache` (TTL 600s, max 128 entries) used by `/query` + `/records`.
  - `/records` **always** requires `query_id` and serves cached results (respecting `limit`).
- **`main.py`** is a thin application factory entry for `uvicorn`.

### 5.7 Utilities & configuration
- **`config.py`** centralizes settings via `pydantic-settings`, auto-loads `.env`, and guarantees the spaCy model is installed (downloading if needed).
- **`utils/logger.py`** provides a lazily configured global logger used project-wide.
- **`utils/file_handler.py`, `utils/helpers.py`, `utils/validators.py`** host reusable filesystem/path helpers, deterministic hashing, and shared validation snippets used outside the FastAPI validators.

---

## 6️⃣ Operational policies & guarantees

1. **Deterministic schema versioning** — versions only increment when `SchemaField` sets change; duplicate uploads reuse the last schema and skip collection recreation.
2. **Extraction transparency** — every upload returns `parsed_fragments_summary` populated by the extractor orchestrator (even on `status="empty"`).
3. **Strict queries** — API rejects free-form strings; payloads must include `filter`, optional `sort`, and `limit` (bounded to 1000).
4. **Idempotent storage** — document validation occurs before insertion; unknown fields or type mismatches are logged + skipped to avoid corrupting collections.
5. **Schema evolution** — `storage.migration` applies additive fields and type fallbacks before persisting new schema versions; diffs are surfaced through `/schema/history`.
6. **NER safety** — NER is enabled by default but wrapped in try/except; outages never block ingestion.
7. **Observability** — request middleware adds `X-Request-ID` + `X-Response-Time-ms`; services log all major transitions (extraction counts, schema evolution decisions, insertion stats).
8. **Environment parity** — configuration values are prefixed with `ETL_` (e.g., `ETL_MONGODB_URI`, `ETL_DATABASE_PREFIX`); FastAPI host/port are configurable.

---

## 7️⃣ API surface (FastAPI)

| Endpoint | Method | Description / Notes |
| --- | --- | --- |
| `/upload` | `POST` | Multipart (`file`, optional `source_id`, optional `version`). Returns `UploadResponse` with schema ID, counts, fragment stats, and `status ∈ {"success","noop","empty"}`. |
| `/schema` | `GET` | Requires `source_id`; returns latest `SchemaMetadata`. 404 if none exists. |
| `/schema/history` | `GET` | Returns chronologically ordered schemas plus computed diffs (`added`, `removed`, `type_changes`). |
| `/query` | `POST` | Body must be dict with `filter`/`limit`/`sort`. Executes via `services.query_service`, caches results, responds with `QueryResult + query_id`. |
| `/records` | `GET` | Requires `source_id` + `query_id` (from `/query`) and optional `limit`. Serves cached results; indicates cache TTL + hit metadata. |
| `/health` | `GET` | Lightweight heartbeat exposing pipeline/storage readiness markers. |

All handlers live in `api/handlers.py`, and validators guard malformed inputs before services execute.

---

## 8️⃣ Testing, docs & developer workflow

- **Tests** live in `tests/` (`test_extractors_smoke.py`, `test_tier_a_pipeline.py`, `test_services_end_to_end.py`, etc.) and exercise extractor logic plus Tier-A happy paths. Run via `pytest`.
- **Documentation** inside `docs/` drills into extractor/normalizer/orchestrator implementations, JSON/KV specifics, schema diff computation, and visualization guides.
- **Setup**: Python 3.11+, create `.venv`, install `requirements.txt`, download spaCy model (`python -m spacy download en_core_web_sm`), configure `.env` (see `.env.example`), then run `uvicorn main:main --reload`.
- **MongoDB**: Provide a reachable URI via `ETL_MONGODB_URI` (local or cloud). Collections are namespaced per source using the configured prefix.
- **Linting/style**: Project stays `ruff`/`black` friendly (not enforced yet). Logging is centralized via `utils.logger`.

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
│   └── orchestrator.py
├── normalizers/
│   ├── base.py
│   ├── json_normalizer.py
│   ├── kv_normalizer.py
│   └── orchestrator.py
├── inference/
│   ├── schema_detector.py
│   ├── type_mapper.py
│   ├── confidence_scorer.py
│   └── schema_generator.py
├── storage/
│   ├── connection.py
│   ├── collection_manager.py
│   ├── document_inserter.py
│   ├── document_retriever.py
│   ├── schema_store.py
│   └── migration.py
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

Keep contributions aligned with these boundaries and principles to preserve determinism, observability, and Tier-A focus. Completed implementation only archive,
read guideline_B.md

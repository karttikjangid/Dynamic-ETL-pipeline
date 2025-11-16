# Dynamic ETL Pipeline

Modular Tier-B pipeline for deterministic ingestion of structured and semi-structured data from `.txt` and `.md` files. Extracts and normalizes JSON objects, key-value pairs, HTML tables, CSV blocks, YAML fragments, and Markdown code blocks. Infers and versions schemas, routes to MongoDB (complex data) or SQLite (tabular data), and exposes strict query endpoints via FastAPI.

## Supported Data Formats

The pipeline extracts and processes the following data formats from `.txt` and `.md` files:

- **JSON Objects**: Structured data in JSON format
- **Key-Value Pairs**: Simple key: value sections
- **HTML Tables**: Tabular data in HTML `<table>` elements
- **CSV Blocks**: Comma-separated values in text blocks
- **YAML Fragments**: YAML-formatted data blocks
- **Markdown Code Blocks**: Fenced code blocks with language hints

## Quick Start

### Prerequisites

- Python 3.11+
- MongoDB instance (development: `mongomock`)
- SQLite (auto-managed)

### Setup

1. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   ```

4. Launch API:
   ```bash
   uvicorn main:main --reload
   ```

5. Run tests:
   ```bash
   pytest
   ```

## Core Workflow

File ingest → Extract → Normalize → Infer Schema → Route → Store → Query

See [`docs/workflow.md`](docs/workflow.md) for detailed data flow, transformations, and technical specifications.

## API Endpoints

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/upload` | `POST` | Multipart file upload with schema inference |
| `/schema` | `GET` | Fetch current schema for a source |
| `/schema/history` | `GET` | Retrieve schema evolution history |
| `/query` | `POST` | Execute Mongo/SQLite queries |
| `/records` | `GET` | Fetch materialized query results |
| `/health` | `GET` | API health check |

**Examples & detailed query syntax:** See [`docs/api_reference.md`](docs/api_reference.md)

## Documentation

Quick links to deep-dive documentation:

- **[API Reference](docs/api_reference.md)** – Complete endpoint documentation with examples
- **[Workflow](docs/workflow.md)** – Pipeline stages, data models, and transformations
- **[Storage Strategy](docs/storage_strategy.md)** – MongoDB vs SQLite routing and versioning
- **[Schema Versioning](docs/schema_versioning.md)** – Schema generation and version management
- **[Design Philosophy](docs/design_philosophy.md)** – Core principles and architecture decisions
- **[Guidelines](guidelines.md)** – Module boundaries and dependency rules
- **[Normalization Guide](docs/normalization_guide.md)** – Data normalization patterns
- **[Test Plan](docs/TEST_PLAN_TIERED.md)** – Testing strategy and validation



## Roadmap

- [ ] **Add storage for raw text content** - currently only structured fragments are stored; implement raw content preservation for full fidelity
- [ ] Implement advanced query builders
- [ ] Add support for additional file formats (PDF, DOCX)

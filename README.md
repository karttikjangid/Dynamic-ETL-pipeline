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

# Named Entity Recognition in the Dynamic ETL Pipeline

## Where NER Runs in the Codebase
- **Service entry point:** `services/ner_service.py` wraps spaCy's `en_core_web_sm` model and exposes `extract_entities_from_text`, `apply_ner_to_fragment`, and `apply_ner_to_fragments` for reuse.
- **Pipeline integration:** `services/pipeline_service.process_upload` calls `apply_ner_to_fragments` immediately after normalization (see the block that sets `evidence["ner"]`). Each normalized fragment is enriched with a `ner` dictionary before routing to MongoDB or SQLite.
- **Schema grouping:** `services/schema_grouping_service.group_tabular_documents` consumes the enriched fragments when clustering SQLite candidates. The `_GroupingBucket` tracks `ner_labels`, so records with similar entities (e.g., PERSON vs. ORG heavy tables) land in the same table, and the resulting `TabularSchemaGroup` stores those labels in `ner_labels` for downstream intelligence.
- **Persisted outputs:** Once NER data is present, it rides along with the serialized documents that `storage.document_inserter` (MongoDB) and `storage.sqlite_document_inserter` write. This means MongoDB records can be queried for entity-aware attributes, and SQLite tables can be post-processed with knowledge of which entity families they contained.

## How the NER Stage Works
1. **Model lifecycle:** `services/ner_service` loads spaCy's small English model once at import time. If the model is missing, it raises a runtime error instructing the operator to run `python -m spacy download en_core_web_sm`.
2. **Per-fragment processing:** `apply_ner_to_fragment` prefers a fragment's `raw_text` (when available) and falls back to `content`. It converts non-string payloads to strings, safely handles `None`, and always returns a copy of the fragment with an added `ner` field.
3. **Entity extraction:** `extract_entities_from_text` feeds the text through spaCy, groups tokens by entity label, deduplicates them (via `set`) and sorts each list so results are deterministic. Common labels include `PERSON`, `ORG`, `GPE`, `DATE`, `MONEY`, etc.
4. **Batch enrichment:** `apply_ner_to_fragments` simply maps the single-fragment helper over a list. The pipeline uses this to enrich every normalized document before storage routing.
5. **Evidence tracking:** `process_upload` records an evidence entry (`evidence["ner"]`) containing the number of fragments enriched or the failure details if spaCy raises.

## Problems NER Solves for the Pipeline
- **Schema-aware clustering:** Tabular fragments (CSV/KV/HTML) often lack explicit headers tying related rows together. By comparing the `ner_labels` sets, `schema_grouping_service` can avoid merging tables whose text refers to different semantic domains (e.g., finance vs. personnel), reducing false table merges.
- **Searchable context:** MongoDB documents keep an embedded `ner` map, enabling downstream query layers (or external analytics) to filter or highlight records mentioning specific entities without re-processing raw text.
- **Audit & explainability:** The per-fragment `ner` payload gives operators visibility into what the pipeline "understood" about each fragment, which is critical when judging Tier-B submissions or debugging normalization drift.
- **Noise filtering:** When fragments consist mostly of narrative text, entity extraction helps distinguish useful fragments (those naming organizations, amounts, dates) from boilerplate, guiding human reviewers or any optional scoring heuristics.

## Verification & Current Status
- Targeted unit coverage lives in `tests/test_ner_service.py` (23 tests). They exercise basic extraction, deduplication, preference for `raw_text`, immutability guarantees, and mixed-content edge cases.
- Latest manual run (executed in this workspace) shows all tests passing:
  ```cmd
  cd "C:\Users\preci\OneDrive\Documents\AuraVerse Final\Dynamic-ETL-pipeline"
  C:\Users\preci\anaconda3\Scripts\conda.exe run -n etl-extractor --no-capture-output python -m pytest tests/test_ner_service.py
  ```
  Output: `23 passed` (dep. warnings only), confirming that the spaCy-backed NER stage is operational in the current repo state.

Use this document as the single reference point for how and why NER participates in the Dynamic ETL pipeline. Update it whenever you change the pipeline stages, entity model, or downstream consumers.

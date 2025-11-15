(read guidelines.md for more context)
# **`guidelines_B.md` — Dynamic ETL Pipeline (Tier A → Tier B Upgrade)**

### **Version: 2.0 — Tier‑B Ready, with SQLite, NER, DeepDiff, and Genson Versioning**

---

# 🚀 **1. Mission**

Build a **deterministic, schema‑evolving ETL pipeline** for unstructured data spanning **Tier‑A and Tier‑B** complexity:

* Tier‑A: JSON, KV, Markdown.
* Tier‑B: messy mixed content (HTML snippets, CSV‑like fragments, partial structures, semi‑structured sections).

The system must automatically ingest → extract → normalize → infer schema → version using **DeepDiff + Genson** → store records in **SQLite** → run strict DB queries.

**Goals:** reliability, determinism, incremental schema evolution, transparent diffs, strong evidence reporting.

**Non‑goals:** natural‑language queries, PDFs/OCR (Tier‑C), complex distributed storage.

---

# 🧩 **2. End‑to‑end pipeline (Tier A + Tier B)**

1. **Upload → /upload**

   * Accepts `.txt` /.md`+ Tier‑B`.txt` containing mixed fragments.
   * Validates MIME & extension.

2. **Extraction layer**

   * Tier‑A Extractors: JSON / KV / fenced blocks.
   * Tier‑B Extractors: HTML snippet detector, CSV heuristics, YAML locator, NER enrichment.
   * Emits **fragment stats**: `{json_fragments, kv_pairs, html_tables, csv_blocks, yaml_blocks, total_records}`.
   * Each extraction includes **offsets**, **token spans**, and **source-type classification**.

3. **Normalization**

   * JSONNormalizer, KVNormalizer, CSVNormalizer, HTMLTableNormalizer.
   * NER attached per fragment: entities = `{PERSON, ORG, PRODUCT, LOCATION, DATE}`.

4. **Schema Inference** using **Genson + custom layer**

   * Genson provides base JSON-schema aggregation.
   * Custom layer attaches: type-confidence, nullable, path, semantic hints.

5. **Schema Versioning** using **DeepDiff + Genson**

   * Compute signature from Genson canonical schema.
   * Compare previous → new via DeepDiff.
   * If diff only cosmetic → keep same version.
   * If structural → increment `schema_v{n+1}`.

6. **Storage → SQLite**

   * Flatten nested fields to SQLite columns.
   * Mixed arrays stored as JSON.
   * Schema change → creates a new SQLite table with name `{source_id}_v{schema_version}`.

7. **Queries → /query**

   * Accepts only SQL‑safe structured queries: `{select, where, limit, order_by}`.
   * Routes to correct SQLite table based on schema version.

---

# 🧱 **3. Schema metadata fields (completed spec)**

Every schema must include:

```
schema_id
source_id
generated_at
compatible_dbs: ["sqlite"]
version
fields: [
  name
  path
  type
  nullable
  example_value
  confidence
  source_offsets
  suggested_index
]
primary_key_candidates
migration_notes
version_diff (DeepDiff output)
```

---

# 📦 **4. Evidence & gaps output (Completed Template)**

Every phase must return a structured evidence block:

| Phase                             | Status summary                           | Evidence & gaps                                                              |
| --------------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------- |
| **0 – Sanity**                    | Fully validated                          | Endpoints live. MIME accepted. SQLite connected.                             |
| **1 – Ingest & Parse (Tier A/B)** | JSON/KV/HTML/CSV extracted with offsets  | Missing advanced CSV dialect detection. HTML parser handles tables only.     |
| **2 – Schema Generation**         | Genson + custom metadata                 | Type mapping improved; SQL type mapping complete; PK suggestions available.  |
| **3 – Evolving Schema**           | DeepDiff detects adds/removes/type flips | No field-regression testing yet.                                             |
| **4 – Type-change & Ambiguity**   | Mixed-type detection working             | Normalization plan uses union-type mapping; needs richer datetime inference. |
| **5 – Mapping to Target DB**      | SQLite SQL DDL emitted                   | No multi-DB export.                                                          |

This evidence block must be included in each `/upload` response.

---

# 🧪 **5. Tier‑B Extractors — required behaviours**

### ✔ HTML snippet extraction

* Detect `<table>...</table>`
* Convert to row arrays.
* Attach `html_table_id` + offsets.

### ✔ CSV block detection

* Regex-based row alignment.
* Infer header.
* Convert to records.

### ✔ Mixed-fragment ties

* Each fragment must include: `fragment_id`, `source_type`, `offset_range`, `cleaned_text`.

---

# 🔧 **6. Versioning Model (DeepDiff + Genson)**

```
schema_raw = genson_schema
prev_schema_raw = last_schema.genson_version

changes = DeepDiff(prev_schema_raw, schema_raw)

if changes.is_empty():
    version stays same
else:
    increment version
    attach `version_diff = changes.to_dict()`
```

---

# 🏛 **7. SQLite Storage Rules**

* Each schema version gets its own table.
* Table name: `{source_id}_v{schema_version}`.
* Columns generated from flattened schema paths.
* Array → JSON text.
* Indexes created for all `suggested_index=True` fields.

---

# 📡 **8. APIs**

## `/upload`

Returns:

```
{
  status,
  source_id,
  file_id,
  schema_id,
  version,
  parsed_fragments_summary,
  evidence,
  schema_metadata
}
```

## `/schema`

Returns latest schema.

## `/schema/history`

Shows all versions and DeepDiff diffs.

## `/query`

Strict structured SQL DSL only.

---

# 🔍 **9. Principles**

* Deterministic.
* Schema evolution = diff-based, not time-based.
* Evidence-first: every step produces measurable stats.
* Extraction never fails silently.
* Normalization produces reversible mapping.
* Storage is versioned, never destructive.
* Queries are strict and safe.

---

# 🧭 **10. Developer Workflow**

* Python 3.11
* SQLite (built-in)
* pip install: `genson`, `deepdiff`, `beautifulsoup4`, `python-dateutil`, `spacy`, `pandas`
* Run: `python -m spacy download en_core_web_sm`

---
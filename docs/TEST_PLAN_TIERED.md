# Tiered Test Plan — Dynamic ETL Pipeline

_Comprehensive validation matrix covering smoke, mixed-format, robustness, and schema-evolution behaviors across the ingestion pipeline._

---

## How to Use This Document

1. Pick the tier that matches your testing depth (A = smoke, D = evolution deep dives).
2. For each test ID, craft/locate the described fixture (input file or dataset).
3. Run the standard automation checklist (see bottom of file) to validate responses from `/upload`, `/schema`, `/schema/history`, `/query`, and `/records`.
4. Log results with priority/severity guidance provided here.

Each test case captures:
- **Purpose** — scenario intent.
- **Input** — file type + brief description of contents.
- **Expected Outcome** — what the pipeline should emit.
- **Acceptance Checks** — concrete assertions (API/status, schema details, metadata, etc.).
- **Automatable** — whether the case can be scripted into CI.
- **Priority / Severity** — suggested triage labels for failures.

---

## Tier A — Simple (Smoke + Basic Parsing)

| ID | Purpose | Input | Expected Outcome | Acceptance Checks | Automatable | Priority | Severity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A-01** | Validate baseline KV + JSON parsing | `.txt` containing `key: value` pairs, a tiny inline JSON block, and a trailing prose sentence | KV pairs captured as structured fields, JSON parsed, prose stored as text fragment | `/upload` returns `200`; `parsed_fragments_summary.kv_pairs = N`, `json_fragments = 1`; `SchemaMetadata` includes KV fields and a `text_fragment` entry | ✅ | `P0` | Major |
| **A-02** | Extract JSON from Markdown code block with heading metadata | `.md` with leading `# Heading` plus ```json``` fenced block | JSON parsed; heading stored as document metadata | Schema exposes JSON fields with `example_values`; response metadata includes heading text | ✅ | `P0` | Major |
| **A-03** | Parse CSV-style data embedded in TXT | `.txt` where each line is `col1,col2,...` | Rows converted into tabular collection; schema columns reflect header row | Record count equals number of CSV lines; `parsed_fragments_summary.table_fragments = 1`; schema typed as table | ✅ | `P0` | Major |
| **A-04** | Handle mini HTML table snippet | `.txt` containing `<table><tr>...</tr></table>` | HTML table normalized into structured rows | `parsed_fragments_summary.html_tables = 1`; schema contains table mapping | ✅ | `P1` | Major |
| **A-05** | Verify PDF text extraction without OCR | Simple text-based PDF | Text extracted as standard fragment; no OCR flag | Upload response states `ocr_applied = false`; schema contains text fields only | ✅ | `P1` | Major |
| **A-06** | Ensure idempotent schema reuse on duplicate uploads | Re-upload exact fixture from A-01 | No schema churn; deterministic `schema_id` reused | `/schema/history` shows single version; duplicate upload references same `schema_id`; no duplicate records inserted | ✅ | `P0` | Major |
| **A-07** | Handle whitespace/encoding-only changes | Same logical document as A-01 but with whitespace or encoding variations | Schema remains identical or semantically equal | Schema diff either absent or empty; normalized hash unchanged | ✅ | `P1` | Minor |
| **A-08** | Surface metadata for malformed JSON | `.txt` with JSON missing a trailing brace | Fragment captured with error metadata and `confidence < 1` | Upload response includes `errors` entry with byte offset; schema marks fields as tentative | ✅ | `P1` | Major |

---

## Tier B — Mixed & Messy (Edge-Case Real-ish)

| ID | Purpose | Input | Expected Outcome | Acceptance Checks | Automatable | Priority | Severity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **B-01** | Validate multi-fragment extraction (JSON + HTML + CSV) | `.txt` mixing inline JSON, an HTML table, and CSV rows | Three fragment groups materialize into discrete collections | `parsed_fragments_summary` counts (`json=1`, `html_tables=1`, `table_fragments=1`); schema metadata links fragments via provenance IDs | ✅ | `P0` | Blocker |
| **B-02** | Parse Markdown YAML frontmatter and inline HTML | `.md` with `---` frontmatter + body containing `<table>` | Frontmatter promoted to metadata; HTML table parsed | Frontmatter keys present in schema metadata with `source_offsets`; HTML mapped to structured table | ✅ | `P1` | Major |
| **B-03** | Handle HTML with comments and `<script>` blocks safely | HTML page fragment containing comments + JS snippets | Scripts treated as code fragments (never executed); textual data extracted | Responses flag `code_fragments` with `language` metadata; ensure no execution side-effects (test harness asserts) | ✅ | `P0` | Blocker |
| **B-04** | Mixed valid + malformed JSON fragments | File with two valid JSON blobs and one malformed block | Valid fragments fully parsed; malformed flagged | Schema includes two confident fragments; third has error details and partial fields | ✅ | `P0` | Major |
| **B-05** | Capture inline SQL/code snippets | Text containing SQL statements and code samples | Code fragments stored with `language` tags, not executed | Upload metadata shows `code_fragments` entries; sandbox verifies zero execution side-effects | ✅ | `P1` | Blocker |
| **B-06** | CSV with inconsistent quoting | CSV section where some rows have mismatched quotes | Parser recovers valid rows, flags problematic ones | `data_quality.parse_issues` lists row numbers; row count matches recoverable rows | ✅ | `P1` | Major |
| **B-07** | Mixed delimiters inside CSV-like block | CSV block mixing commas/semicolons | Delimiter heuristic picks dominant separator; schema consistent | `confidence.delimiter` present; parsed rows align with expected canonicalization | ✅ | `P1` | Major |
| **B-08** | Markdown nested lists + inline JSON-like lines | `.md` with nested bullets referencing JSON fragments | List hierarchy preserved, JSON extracted | Schema metadata includes path mapping (`$.list[0].subitem`); JSON fields typed | ✅ | `P2` | Minor |
| **B-09** | Timezone and date-format ambiguity | File containing multiple date/time formats | Dates normalized toward ISO; ambiguity flagged | Schema field type `date` with `normalization_hint`; confidence values per format | ✅ | `P0` | Major |
| **B-10** | Heterogeneous key-value separators | Block using `:`, `=`, and `-` as separators | Canonical KVP extraction with deduped keys | Schema shows merged field names with sample values per variant | ✅ | `P1` | Major |

---

## Tier C — Real-world Noise (Robustness + Performance)

| ID | Purpose | Input | Expected Outcome | Acceptance Checks | Automatable | Priority | Severity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C-01** | Scraped HTML with duplicated fields | Large HTML dump with repeated `price`, `title`, noisy banners | Dedupe logic consolidates repeated fields with provenance | Schema entries have `sources` arrays + per-value confidence | ✅ | `P0` | Blocker |
| **C-02** | PDF requiring OCR with noise | Scanned PDF (includes OCR typos like `l0cation`) | OCR triggered; confidence + normalization hints recorded | Upload metadata `ocr_applied = true`; `ocr_confidence` and spell-correction suggestions present | ⚠️ Partial (OCR quality scoring can be automated) | `P0` | Blocker |
| **C-03** | Multi-lingual text fragments | Text mixing English + second language | Language detection per fragment; encoding preserved | Schema metadata includes `lang` tags; no mojibake | ✅ | `P1` | Major |
| **C-04** | Inconsistent numeric formats | Values like `9,99`, `$9.99`, `9.9900` | Normalized decimal representation + currency inference | Schema type `decimal`, `original_raw` stored, currency metadata added | ✅ | `P1` | Major |
| **C-05** | Conflicting values across JSON-LD + KV | File with JSON-LD block and separate KV price | Conflict resolution recorded with priority rules | `schema.metadata.provenance` shows both sources; `migration_notes` capture resolution | ✅ | `P0` | Blocker |
| **C-06** | PDF with repeated headers/footers | Multi-page PDF repeating boilerplate | Headers/footers stripped from final fragments | Content length reduced; tests assert absence of footer text in normalized output | ✅ | `P1` | Major |
| **C-07** | JS-generated content capture | HTML where JSON lives inside `<script>var data=...` | Script JSON extracted and parsed; script flagged | Schema shows parsed object; script fragment recorded | ✅ | `P1` | Major |
| **C-08** | Ambiguous boolean/numeric representations | Values like `"true"`, `0`, `"N/A"` | Union typing or canonical conversion with `data_quality` flags | Schema lists union types or canonical bool; `nullable_reason` for `"N/A"` | ✅ | `P1` | Major |
| **C-09** | Large file stress (50–100 MB) | Huge scraped dump | Streaming ingestion succeeds within SLA; no OOM | Harness records ingestion latency, memory footprint < limit | ✅ | `P0` | Blocker |
| **C-10** | Injection-like content detection | Text containing `DROP TABLE`, SQL/JS injection payloads | Content stored safely, execution prevented, flagged as code | `code_fragments` flagged; security audits confirm zero execution | ✅ | `P0` | Blocker |

---

## Tier D — Schema Evolution & Migration (Backward Compatibility)

Each scenario builds upon Tier C-level realism. Produce fixtures with explicit **versioned uploads** (`source_id` fixed, `version` increments). For each ID below, craft at least six concrete variants (v1…vN) demonstrating the described evolution pattern; capture diffs via `/schema/history` and assert migration rules.

| ID | Evolution Theme | Variant Guidance | Expected Outcome | Acceptance Checks | Automatable | Priority | Severity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **D-01** | Add simple field | v1 baseline → v2 introduces `metadata.source_version`; extend to v6 by adding other scalar metadata knobs | Schema diff shows additive fields only; defaults set to null | `/schema/history` diff contains `+ metadata.source_version`; migration notes mention default behavior; legacy queries unaffected | ✅ | `P1` | Major |
| **D-02** | Add nested field | Extend `pricing` with `discounts[]` nested array across versions | Nested structures added without breaking existing paths | Schema diff flags nested addition; queries for pre-existing fields still succeed | ✅ | `P1` | Major |
| **D-03** | Rename with mapping | Transition `price_usd` → `price` + `currency`; include follow-up versions where currency varies | Rename captured with mapping metadata; derived rules stored | `migration_notes` describe aliasing; historical `price_usd` queries re-routed | ✅ | `P0` | Major |
| **D-04** | Type flip (string → number) | Convert `views` from string digits to integer; later to float | Schema handles coercion; `data_quality` logs coercion counts | Numeric filters operate across all versions; coercion warnings captured | ✅ | `P0` | Major |
| **D-05** | Type ambiguity with `N/A` | Introduce `N/A` values mixed with numerics | Nullability and `nullable_reason` recorded | Queries treat `N/A` as null; schema union type documented | ✅ | `P1` | Major |
| **D-06** | Array → Object | Transform `tags: []` → `tags: {primary, extras[]}`; extend with additional nesting | Migration doc details mapping; union handling validated | `/schema/history` diff shows structural flip; query compatibility logic validated | ✅ | `P0` | Blocker |
| **D-07** | Object → Array | Reverse of D-06 with additional splits/merges in later versions | Array structure introduced with back-compat strategy | Migration plan ensures old object queries still resolvable | ✅ | `P0` | Blocker |
| **D-08** | Field deletion | Remove `legacy_id` and archive value | Schema history lists removal; archived access path documented | Legacy query returns archived value or gracefully errors with guidance | ✅ | `P0` | Major |
| **D-09** | Semantic change | Re-scale `rating` (1–5) to 0–1 float, later to percentage | Semantic change flagged with formula | Migration notes describe mapping; queries adjusted using formula | ✅ | `P1` | Major |
| **D-10** | Field split | Split `full_name` into `first_name` + `last_name` and add `middle_initial` later | Schema diff shows removal + additions with derived logic | `/schema/history` includes `split` annotation; old queries rebuilt via concatenation | ✅ | `P1` | Major |
| **D-11** | Field merge | Merge `city` + `state` into `location` object, then add `geo` field | Merge mapping + provenance recorded | Query compatibility verified by decomposing `location` | ✅ | `P1` | Major |
| **D-12** | Multi-step evolution marathon | Build v1→v6 sequence combining renames, type flips, nested adds, deletions | Full schema history traceable; earlier version queries runnable against v6 | Regression queries from v2/v3 succeed against v6 via migrations; diffs logged for each step | ✅ | `P0` | Blocker |

> **Variant Tracking:** maintain fixture directories per scenario (e.g., `fixtures/evolution/D-03/v1.json`, `v2.json`, …). Tests should upload sequential versions, call `/schema/history`, and assert migration metadata.

---

## Additional Metadata & Guidance

### Priority & Severity Cheatsheet

- **Priority:** `P0` (core parsing / safety), `P1` (schema correctness), `P2` (observability/perf).
- **Severity:** `Blocker` (pipeline unsafe/unusable), `Major` (schema wrong but pipeline runs), `Minor` (metadata mismatch).

### Ground-Truth Fixtures

- Tier A/B: pair input files with expected normalized JSON dumps for easy diffing.
- Tier C: include OCR-corrected transcripts, deduplicated reference outputs, and perf budgets.
- Tier D: store expected schema documents per version plus diff JSON for regression assertions.

### Score Weighting (for dashboards)

| Dimension | Weight |
| --- | --- |
| Parsing fidelity | 30% |
| Schema accuracy | 25% |
| Evolution handling | 20% |
| Query/LLM validation | 15% |
| Robustness & security | 10% |

### Quick-run Automation Checklist ✅

1. **Upload** fixture via `/upload` (assert `200/201` and inspect `parsed_fragments_summary`).
2. **Fetch schema** via `/schema?source_id=` and compare to expected fields/types/confidence.
3. **Diff history** via `/schema/history?source_id=` (tier D focus) and assert migrations.
4. **Run queries** — either strict payloads or NL→LLM→query flow; verify `/query` + `/records` outputs.
5. **Idempotency** — re-upload identical or whitespace-variant files (A-06/A-07) and confirm no schema churn.
6. **Stress/perf** — for Tier C large files, log ingestion latency, memory, and timeout behavior.

---

## Next Steps

- Automate Tier A/B inside CI (fixtures live under `tests/payloads.py`).
- Schedule Tier C/D via nightly jobs or manual release gates.
- Keep this plan updated alongside extractor/normalizer/inference changes.

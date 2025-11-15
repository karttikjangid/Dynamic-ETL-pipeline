# **`guidelines.md` — Dynamic ETL Pipeline (Tier-A Only)**

### **Version: Final**

### **Scope: Strict JSON/KV Extraction → Normalization → Schema Inference → MongoDB Storage → Query Execution (Strict Queries Only)**

---

# 1️⃣ Project Goal

Build a **modular, deterministic, schema-evolving ETL pipeline** that ingests `.txt` and `.md` files containing:

* JSON blobs
* Key–value pairs
* Raw text paragraphs
* Markdown JSON code blocks

The pipeline must:

1. **Extract** structured data fragments
2. **Normalize** them
3. **Infer a stable schema**
4. **Store records in MongoDB**
5. **Allow strict Mongo/SQL queries via an API**
6. **Handle re-uploads deterministically (no fake schema churn)**

Only **Tier-A complexity** is targeted — meaning no HTML tables, no CSVs, no malformed inputs, no schema reconciliation beyond basic versioning.

---

# 2️⃣ Architectural Overview

### **Modules (strict boundaries):**

1. **extractors/**
2. **normalizers/**
3. **inference/**
4. **storage/**
5. **services/**
6. **api/**
7. **core/** (shared models, exceptions, constants)
8. **utils/** (helpers, validators, file handlers)

### **Dependency Rules (MUST FOLLOW)**

```
main.py → api → services → extractors/normalizers/inference/storage  
core/ is allowed everywhere  
utils/ allowed everywhere  
❌ extractors → services  (never)  
❌ storage → extractors  (never)  
```

---

# 3️⃣ Full Folder Structure

```
project/
│
├── main.py
├── config.py
├── requirements.txt
├── .env.example
│
├── core/
│   ├── models.py
│   ├── constants.py
│   ├── exceptions.py
│   └── __init__.py
│
├── extractors/
│   ├── base.py
│   ├── file_parser.py
│   ├── json_extractor.py
│   ├── kv_extractor.py
│   ├── orchestrator.py
│   └── __init__.py
│
├── normalizers/
│   ├── base.py
│   ├── json_normalizer.py
│   ├── kv_normalizer.py
│   ├── orchestrator.py
│   └── __init__.py
│
├── inference/
│   ├── schema_detector.py
│   ├── type_mapper.py
│   ├── confidence_scorer.py
│   ├── schema_generator.py
│   └── __init__.py
│
├── storage/
│   ├── base.py
│   ├── connection.py
│   ├── collection_manager.py
│   ├── document_inserter.py
│   ├── document_retriever.py
│   ├── schema_store.py
│   ├── migration.py
│   └── __init__.py
│
├── services/
│   ├── pipeline_service.py
│   ├── schema_service.py
│   ├── query_service.py
│   ├── orchestrator.py
│   └── __init__.py
│
├── api/
│   ├── routes.py
│   ├── handlers.py
│   ├── validators.py
│   ├── middleware.py
│   └── __init__.py
│
└── utils/
    ├── logger.py
    ├── file_handler.py
    ├── validators.py
    ├── helpers.py
    └── __init__.py
```

---

# 4️⃣ Core Principles

### **Modularity**

Each module has exactly ONE responsibility.

### **Loose Coupling**

All modules communicate through **Pydantic models** in core/models.py.

### **Deterministic Schema Versioning**

* Schema version increments **ONLY IF** fields change.
* Re-uploading identical content MUST NOT create new versions.
* `schema_id = f"{source_id}_v{version}"`

### **No Natural Language Queries**

API only accepts strict MongoDB or SQL-like dict queries.

### **Extraction Summaries Required**

Upload response must include:

```
{
  "json_fragments": X,
  "kv_pairs": Y
}
```

---

# 5️⃣ **CORE MODULE**

## `core/models.py`

### **(all classes fully defined)**

```python
class ExtractedRecord(BaseModel):
    data: Dict[str, Any]
    source_type: str  # "json" or "kv"
    confidence: float = 1.0


class NormalizedRecord(BaseModel):
    data: Dict[str, Any]
    original_source: str
    extraction_confidence: float


class SchemaField(BaseModel):
    name: str
    type: str
    nullable: bool = True
    example_value: Optional[Any] = None
    confidence: float = 1.0
    source_path: Optional[str] = None


class SchemaMetadata(BaseModel):
    schema_id: str
    source_id: str
    version: int
    fields: List[SchemaField]
    generated_at: datetime
    compatible_dbs: List[str] = ["mongodb"]
    record_count: int
    extraction_stats: Dict[str, int]


class SchemaDiff(BaseModel):
    added_fields: List[str]
    removed_fields: List[str]
    type_changes: Dict[str, Dict[str, str]]
    migration_notes: str


class UploadResponse(BaseModel):
    status: str
    source_id: str
    file_id: str
    schema_id: str
    records_extracted: int
    records_normalized: int
    parsed_fragments_summary: Dict[str, int]


class GetSchemaResponse(BaseModel):
    schema: SchemaMetadata
    compatible_dbs: List[str]


class GetSchemaHistoryResponse(BaseModel):
    schemas: List[SchemaMetadata]
    diffs: List[SchemaDiff]


class GetRecordsResponse(BaseModel):
    count: int
    records: List[Dict[str, Any]]
    source_id: str


class QueryResult(BaseModel):
    query: Dict[str, Any]
    results: List[Dict[str, Any]]
    result_count: int
    execution_time_ms: float
```

---

# 6️⃣ **EXTRACTORS**

## `extractors/base.py`

```python
class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, content: str) -> List[ExtractedRecord]:
        pass
```

## `extractors/file_parser.py`

```python
def parse_file(file_path: str) -> str: ...
def parse_txt_file(file_path: str) -> str: ...
def parse_md_file(file_path: str) -> str: ...
def extract_code_blocks(md_content: str) -> List[str]: ...
```

## `extractors/json_extractor.py`

```python
class JSONExtractor(BaseExtractor):
    def extract(self, content: str) -> List[ExtractedRecord]: ...


def extract_json_fragments(text: str) -> List[Dict[str, Any]]: ...
def find_json_patterns(text: str) -> List[str]: ...
def parse_json_string(json_str: str) -> Optional[Dict]: ...
```

## `extractors/kv_extractor.py`

```python
class KVExtractor(BaseExtractor):
    def extract(self, content: str) -> List[ExtractedRecord]: ...


def extract_key_value_pairs(text: str) -> List[Dict[str, str]]: ...
def find_kv_sections(text: str) -> List[str]: ...
def parse_kv_line(line: str) -> Optional[tuple[str, str]]: ...
```

## `extractors/orchestrator.py`

```python
def extract_all_records(file_path: str) -> tuple[List[Dict], Dict[str, int]]: ...
def combine_extracted_records(json_records, kv_records) -> List[Dict]: ...
def log_extraction_stats(stats: Dict[str, int]) -> None: ...
```

---

# 7️⃣ **NORMALIZERS**

## base

```python
class BaseNormalizer(ABC):
    @abstractmethod
    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
        pass
```

## json_normalizer.py

```python
class JSONNormalizer(BaseNormalizer):
    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]: ...


def normalize_json_record(record: Dict) -> Optional[Dict]: ...
def validate_json_record(record: Dict) -> bool: ...
def clean_json_values(record: Dict) -> Dict: ...
```

## kv_normalizer.py

```python
class KVNormalizer(BaseNormalizer):
    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]: ...


def normalize_kv_record(record: Dict[str, str]) -> Optional[Dict]: ...
def infer_value_type(value: str) -> Any: ...
def standardize_key_names(record: Dict) -> Dict: ...
```

## orchestrator.py

```python
def normalize_all_records(raw_records: List[Dict]) -> List[Dict]: ...
def categorize_records(records: List[Dict]) -> Dict[str, List[Dict]]: ...
def normalize_by_type(records: List[Dict], source_type: str) -> List[Dict]: ...
```

---

# 8️⃣ **INFERENCE MODULE**

## schema_detector.py

```python
def detect_data_types(records: List[Dict]) -> Dict[str, str]: ...
def load_records_to_dataframe(records: List[Dict]) -> pd.DataFrame: ...
def infer_arrow_schema(df) -> pa.Schema: ...
def extract_field_types(arrow_schema) -> Dict[str, str]: ...
```

## type_mapper.py

```python
def map_pyarrow_to_app_type(type_str: str) -> str: ...
def get_type_mapping() -> Dict[str, str]: ...
```

## confidence_scorer.py

```python
def calculate_field_confidence(records, field_name, detected_type) -> float: ...
def count_field_occurrences(records, field_name) -> int: ...
def check_type_consistency(records, field_name, expected_type) -> float: ...
```

## schema_generator.py

```python
def generate_schema(records, source_id, version=1) -> SchemaMetadata: ...
def build_schema_fields(records, field_types, field_confidences) -> List[SchemaField]: ...
def extract_example_values(records, field_names) -> Dict[str, Any]: ...
```

---

# 9️⃣ **STORAGE MODULE**

## base.py

```python
class BaseStorage(ABC):
    @abstractmethod
    def create_collection(self, name, schema) -> bool: ...
    @abstractmethod
    def insert_documents(self, name, docs) -> int: ...
    @abstractmethod
    def get_documents(self, name, limit, filter_query=None) -> List[Dict]: ...
    @abstractmethod
    def execute_query(self, name, query) -> List[Dict]: ...
```

## connection.py

```python
class MongoConnection:
    def __init__(self, uri=None): ...
    def connect(self): ...
    def disconnect(self): ...
    def get_client(self): ...
    def get_database(self, name): ...
    @staticmethod
    def get_instance(): ...
```

## collection_manager.py

```python
def create_collection_from_schema(db, name, schema) -> bool: ...
def build_mongo_validation_schema(schema: SchemaMetadata) -> Dict: ...
def create_indexes(db, name, field_names): ...
def alter_collection_add_field(db, name, field_name, field_type) -> bool: ...
```

## document_inserter.py

```python
def insert_documents(db, name, docs) -> int: ...
def batch_insert_documents(db, name, docs, batch_size=100) -> int: ...
def validate_document_for_insertion(doc, schema) -> bool: ...
```

## document_retriever.py

```python
def get_documents(db, name, limit=100, filter_query=None) -> List[Dict]: ...
def count_documents(db, name, filter_query=None) -> int: ...
def get_document_by_id(db, name, doc_id) -> Optional[Dict]: ...
```

## schema_store.py

```python
def store_schema(db, schema) -> bool: ...
def retrieve_schema(db, source_id, version=None) -> Optional[SchemaMetadata]: ...
def get_schema_history(db, source_id) -> List[SchemaMetadata]: ...
def get_latest_schema_version(db, source_id) -> int: ...
```

## migration.py

```python
def detect_schema_change(old, new) -> SchemaDiff: ...
def find_added_fields(old_fields, new_fields) -> List[str]: ...
def find_removed_fields(old_fields, new_fields) -> List[str]: ...
def find_type_changes(old_schema, new_schema) -> Dict[str, Dict[str, str]]: ...
def evolve_collection_schema(db, name, old_schema, new_schema) -> bool: ...
```

---

# 🔟 **SERVICES MODULE**

## pipeline_service.py

```python
def process_upload(file_path, source_id) -> UploadResponse: ...
def get_database_name(source_id) -> str: ...
def get_collection_name(source_id) -> str: ...
```

## schema_service.py

```python
def get_current_schema(source_id) -> SchemaMetadata: ...
def get_schema_history(source_id) -> GetSchemaHistoryResponse: ...
def handle_schema_evolution(source_id, old_schema, new_schema) -> bool: ...
```

## query_service.py

```python
def execute_query(source_id: str, query: Dict[str, Any]) -> QueryResult: ...
```

## orchestrator.py

```python
def get_db_and_collection(source_id) -> tuple[str, str]: ...
def handle_duplicate_upload(source_id, new_schema) -> bool: ...
```

---

# 1️⃣1️⃣ **API MODULE**

## routes.py

Endpoints:

```
POST /upload
GET  /schema
GET  /schema/history
GET  /records
POST /query
GET  /health
```

All handlers are defined in `handlers.py`.

---

# 1️⃣2️⃣ **UTILITIES**

All common helpers (logging, file handling, validators, flattening).

---
Testing will not be done yet as we are only focusing on building it 
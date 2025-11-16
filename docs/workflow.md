# ETL Pipeline Workflow & Data Models

This document outlines the complete workflow of the Dynamic ETL Pipeline, from file upload to data storage, including all custom class objects and their detailed specifications.

## Complete Workflow Overview

```
File Upload → Extraction → Normalization → Schema Generation → Duplicate Detection → Storage Routing → Data Persistence
     ↓            ↓            ↓               ↓                    ↓                ↓              ↓
   HTTP API    Parsers     Cleaners      Inference         Signatures       Backends      MongoDB/SQLite
```

## Phase 1: File Upload & API Layer

### API Endpoints
- **POST `/upload`**: Accepts multipart file upload with optional `source_id` and `version`
- **GET `/schema`**: Retrieves current schema for a source
- **GET `/schema/history`**: Returns schema evolution history with diffs
- **POST `/query`**: Executes strict MongoDB/SQL-like queries
- **GET `/records`**: Fetches paginated query results
- **GET `/health`**: System readiness check

### Request/Response Objects

#### `UploadResponse`
```python
class UploadResponse(BaseModel):
    status: str                                    # "success", "empty", "noop"
    source_id: str                                 # Data source identifier
    file_id: str                                   # UUID for uploaded file
    schema_id: str                                 # Generated schema identifier
    version: int                                   # Schema version number
    records_extracted: int                         # Raw records from extraction
    records_normalized: int                        # Records after normalization
    parsed_fragments_summary: Dict[str, int]       # {"json_fragments": X, "kv_pairs": Y}
    evidence: Optional[Dict[str, Any]]            # Phase-by-phase execution evidence
    schema_metadata: Optional[SchemaMetadata]     # Full schema details
```

#### `QueryResult`
```python
class QueryResult(BaseModel):
    query: Dict[str, Any]                          # Original query payload
    results: List[Dict[str, Any]]                  # Query results
    result_count: int                              # Number of results
    execution_time_ms: float                       # Query execution time
```

## Phase 2: Data Extraction

### ExtractedRecord
```python
class ExtractedRecord(BaseModel):
    data: Union[Dict[str, Any], List[Dict[str, Any]]]  # Single record or table rows
    source_type: str                                   # "json", "kv", "html_table", "csv_block", "yaml_block"
    confidence: float = 1.0                           # Extraction confidence score
    metadata: Optional[Dict[str, Any]] = None         # Fragment metadata (offsets, IDs)
```

### Extraction Process
1. **File Parsing**: `extractors/file_parser.py` handles `.txt` and `.md` files
2. **Fragment Detection**: Identifies JSON blocks, key-value sections, code blocks
3. **Type Classification**: Assigns source types based on detected patterns
4. **Confidence Scoring**: Rates extraction reliability

## Phase 3: Data Normalization

### NormalizedRecord
```python
class NormalizedRecord(BaseModel):
    data: Dict[str, Any]                              # Normalized data dictionary
    source_type: str                                  # Source type after normalization
    extraction_confidence: float                      # Confidence from extraction phase
    provenance: Optional[Dict[str, Any]] = None      # Source tracking information
```

### Normalization Orchestration
- **JSON Normalizer**: `normalizers/json_normalizer.py`
  - Validates dict-shaped payloads
  - Recursively cleans nested values
  - Performs lightweight type inference

- **KV Normalizer**: `normalizers/kv_normalizer.py`
  - Standardizes keys (lowercase + underscores)
  - Strips special characters
  - Infers primitive types and dates

## Phase 4: Schema Generation

### SchemaMetadata (Core Schema Object)
```python
class SchemaMetadata(BaseModel):
    schema_id: str                                    # Unique identifier: {source_id}_v{version}_{uuid}
    source_id: str                                    # Data source identifier
    version: int                                      # Schema version number
    fields: List[SchemaField]                         # Field definitions
    generated_at: datetime                            # Schema creation timestamp
    compatible_dbs: List[str] = ["mongodb"]           # Compatible storage backends
    record_count: int                                 # Records used for inference
    extraction_stats: Dict[str, Union[int, float]]    # Processing statistics
    primary_key_candidates: Optional[List[str]] = None # Potential PK fields
    migration_notes: Optional[str] = None             # Schema evolution notes
    version_diff: Optional[Dict[str, Any]] = None     # DeepDiff results
    genson_schema: Optional[Dict[str, Any]] = None    # JSON Schema for versioning
```

### SchemaField (Individual Field Definition)
```python
class SchemaField(BaseModel):
    name: str                                          # Field name
    path: Optional[str] = None                         # Nested path (e.g., "user.address.city")
    type: str                                          # Data type: string, integer, number, boolean, object, array
    nullable: bool = True                             # Whether field can be null
    example_value: Optional[Any] = None               # Sample value for documentation
    confidence: float = 1.0                           # Type inference confidence
    source_offsets: Optional[List[int]] = None        # Source location hints
    suggested_index: bool = False                     # SQLite index recommendation
    source_path: Optional[str] = None                 # Legacy path support
```

### Schema Generation Process
1. **Type Detection**: `detect_data_types()` analyzes records for field types
2. **Confidence Calculation**: `calculate_field_confidence()` scores type reliability
3. **Genson Schema**: `generate_genson_schema()` creates JSON Schema for signatures
4. **Field Building**: `build_schema_fields()` constructs SchemaField objects

## Phase 5: Duplicate Detection & Versioning

### SchemaDiff (Change Tracking)
```python
class SchemaDiff(BaseModel):
    added_fields: List[str]                           # Newly added field names
    removed_fields: List[str]                         # Removed field names
    type_changes: Dict[str, Dict[str, str]]          # Field type changes
    migration_notes: str                              # Human-readable change summary
```

### Versioning Logic
1. **Signature Generation**: Create deterministic hash of schema structure
2. **Comparison**: Compare new vs existing schema signatures
3. **Decision**: Reuse version if identical, increment if different
4. **Migration**: Apply schema evolution procedures when needed

## Phase 6: Storage Routing & Persistence

### Storage Categorization
```python
# Records categorized by storage backend compatibility
categorized = categorize_records_by_storage(normalized_records)
mongodb_records = categorized["mongodb"]     # Complex/nested data
sqlite_records = categorized["sqlite"]       # Tabular data
```

### MongoDB Storage
- **Collection Naming**: `{source_id}_records`
- **Schema Validation**: JSON Schema with `bsonType` constraints
- **Indexing**: Automatic field indexes for query performance
- **Data Preservation**: Native BSON maintains full document structure

### SQLite Storage
- **Table Naming**: `{source_id}_v{version}`
- **Schema Creation**: Dynamic DDL generation from SchemaMetadata
- **Data Flattening**: Nested objects converted to flat columns
- **Type Mapping**: Schema types mapped to SQL types (TEXT, INTEGER, REAL, etc.)

## Data Flow Summary

### Input → Processing → Output Chain

1. **Raw File** → **ExtractedRecord[]**
   - File parsing → Structured fragments

2. **ExtractedRecord[]** → **NormalizedRecord[]**
   - Type-aware cleaning → Standardized data

3. **NormalizedRecord[]** → **SchemaMetadata**
   - Statistical analysis → Type inference + confidence

4. **SchemaMetadata** → **Version Decision**
   - Signature comparison → Version reuse/increment

5. **NormalizedRecord[] + SchemaMetadata** → **Storage Assignment**
   - Type + structure analysis → MongoDB vs SQLite routing

6. **Storage Assignment** → **Persistent Data**
   - Backend-specific formatting → Database storage

## Error Handling & Validation

### Validation Objects
```python
class GetSchemaResponse(BaseModel):
    schema_data: SchemaMetadata
    compatible_dbs: List[str]

class GetSchemaHistoryResponse(BaseModel):
    schemas: List[SchemaMetadata]
    diffs: List[SchemaDiff]

class GetRecordsResponse(BaseModel):
    count: int
    records: List[Dict[str, Any]]
    source_id: str
```

### Exception Types
- `ExtractionError`: File parsing failures
- `NormalizationError`: Data cleaning issues
- `SchemaInferenceError`: Type inference problems
- `StorageError`: Database operation failures
- `PipelineError`: General pipeline issues
- `QueryExecutionError`: Query processing failures

## Performance Characteristics

### Processing Metrics Tracked
- **Extraction Stats**: Fragment counts, parsing success rates
- **Schema Stats**: Field counts, confidence averages, type distributions
- **Storage Stats**: Insert counts, batch sizes, timing
- **Query Stats**: Execution time, result counts, pagination metrics

### Optimization Strategies
- **Batch Processing**: Large datasets processed in configurable chunks
- **Lazy Loading**: Schema history and large result sets paginated
- **Indexing**: Automatic index creation on queryable fields
- **Caching**: Query result caching with TTL for repeated requests

## Configuration & Environment

### Core Settings
- **Database Connections**: MongoDB URI, SQLite path
- **Batch Sizes**: Processing chunk sizes for performance
- **Timeouts**: Query execution limits
- **Logging**: Structured logging levels and formats

### Environment Variables
- `MONGODB_URI`: Database connection string
- `MONGODB_DATABASE`: Target database name
- `LOG_LEVEL`: Logging verbosity
- `BATCH_SIZE`: Processing batch size
- `MAX_SCHEMA_FIELDS`: Schema complexity limits

This workflow ensures deterministic, scalable, and intelligent ETL processing with comprehensive data lineage tracking and flexible storage options.
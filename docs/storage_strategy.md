# Storage Strategy & Implementation

This document provides detailed information about the hybrid storage architecture, data routing logic, and backend implementations.

## Overview

The pipeline employs a **hybrid multi-backend approach** with intelligent data routing between MongoDB (complex/nested data) and SQLite (tabular data) based on source type and data structure analysis.

## Storage Backends

| Backend | Purpose | Data Types | Schema Handling | Versioning | Location |
|---------|---------|------------|-----------------|------------|----------|
| **MongoDB** | Complex/nested data | `json`, `yaml_block` | JSON Schema validation | Schema-level versioning | Collections: `{source_id}_records` |
| **SQLite** | Tabular/structured data | `html_table`, `csv_block`, `kv` | Relational tables grouped per schema | DB-per-version, table-level | File: `data/sqlite/{source_id}/v{version}.db` |

## Data Routing Criteria

### Primary: Source Type Classification
- `json`, `yaml_block` → MongoDB (preserves nesting)
- `html_table`, `csv_block`, `kv` → SQLite (relational optimization)

### Secondary: Data Structure Flatness
- Flat schemas (no `object`/`array` types) → SQLite compatible
- Complex schemas → MongoDB required

## Storage Implementation Details

### MongoDB Collections

#### Naming Convention
- **Format**: `{source_id}_records`
- **Example**: `user_data_records`, `api_logs_records`

#### Schema Validation
- JSON Schema with `bsonType` constraints
- Automatic validation on insert operations
- Type safety for complex nested structures

#### Indexing Strategy
- Automatic indexes on all schema fields
- Optimized for query performance
- Compound indexes for common query patterns

#### Data Preservation
- Native BSON documents maintain full structure
- Nested objects and arrays preserved
- No data flattening or loss

### SQLite Tables

#### Naming Convention
- **Format**: `{source_id}_v{version}`
- **Example**: `user_data_v1`, `api_logs_v2`

#### Dynamic Schema Creation
- DDL generation from `SchemaMetadata`
- Typed columns with appropriate SQL types
- Foreign key relationships where applicable

#### Data Flattening
- Nested objects flattened with underscore separators
- `user.address.city` → `user_address_city`
- Array fields handled as separate tables when needed

#### Storage Location
- **Database Files**: `./data/sqlite/{source_id}/v{version}.db`
- **One file per schema version**; files are created lazily when SQLite fragments exist
- Automatic directory creation (customize base via `ETL_SQLITE_BASE_DIR`)

#### Table Grouping (NER-aware)
- Each SQLite-eligible fragment computes a signature using normalized field names + detected NER labels.
- Fragments with Jaccard similarity ≥ 0.7 on fields **and** ≥ 0.5 on labels reuse the same table; everything else spawns additional tables within the same version DB.
- Table names follow `{safe_source}_v{version}_{signature[:8]}` ensuring deterministic reuse.
- Per-table schema metadata is persisted inside `SchemaMetadata.tabular_groups`, allowing downstream services (e.g., queries) to enumerate available tables.

## Schema Compatibility Determination

The pipeline now infers **two schemas per upload**:

1. A **primary schema** built from *all* normalized fragments (used for MongoDB storage, schema history, and versioning).
2. A **tabular schema** built strictly from fragments routed to SQLite (`html_table`, `csv_block`, `kv`).

This decoupling means nested JSON/YAML no longer prevents tabular data from landing in SQLite. Compatibility is derived from both schemas:

```python
def get_compatible_dbs_for_schema(
    schema: SchemaMetadata,
    sqlite_schema: Optional[SchemaMetadata] = None
) -> List[str]:
    """Determine which databases are compatible with a schema."""

    compatible: List[str] = []

    def _is_flat(target: SchemaMetadata) -> bool:
        return all(field.type not in ["object", "array"] for field in target.fields)

    if schema and _is_flat(schema):
        compatible.append("sqlite")                   # Global schema is flat

    if "sqlite" not in compatible and sqlite_schema and _is_flat(sqlite_schema):
        compatible.append("sqlite")                   # Tabular subset is flat

    compatible.append("mongodb")                      # Always supported
    return compatible
```

When a tabular schema exists, SQLite inserts proceed even if the global schema contains nested fields. Only the tabular schema is used for `CREATE TABLE` statements, while the primary schema continues to drive MongoDB collection creation and schema history.

## Versioning Mechanism

### Schema Signatures
**Schema signatures** determine version changes, not upload frequency:

- **Genson-based structural hashing**
- **Duplicate Detection**: Identical signatures reuse existing versions
- **Change Triggers**: Field additions/removals, type changes, nullability shifts

### Version Increment Logic
```python
# Version increment logic
target_version = 1
duplicate_upload = False
if existing_schema is not None:
    duplicate_upload = handle_duplicate_upload(source_id, new_schema, existing_schema)
    target_version = existing_schema.version if duplicate_upload else existing_schema.version + 1
```

## Storage Router Implementation

### Record Categorization
```python
def categorize_records_by_storage(
    records: List[NormalizedRecord]
) -> Dict[str, List[NormalizedRecord]]:
    """Categorize records into MongoDB vs SQLite based on source_type."""

    mongodb_records = []
    sqlite_records = []

    for record in records:
        source_type = record.source_type

        # Route based on source type
        if source_type in ["json", "yaml_block"]:
            mongodb_records.append(record)
        elif source_type in ["html_table", "csv_block", "kv"]:
            sqlite_records.append(record)
        else:
            # Default: check data shape
            if _is_flat_structure(record.data):
                sqlite_records.append(record)
            else:
                mongodb_records.append(record)

    return {
        "mongodb": mongodb_records,
        "sqlite": sqlite_records
    }
```

## Performance Characteristics

### MongoDB Advantages
- **Complex Queries**: Rich query capabilities for nested data
- **Scalability**: Horizontal scaling with sharding
- **Flexibility**: Schema-less design for evolving data

### SQLite Advantages
- **Performance**: Fast queries on tabular data
- **Simplicity**: Single file, no server management
- **Portability**: Easy backup and transfer
- **ACID Compliance**: Full transactional support

## Migration & Evolution

### Schema Evolution
- **Automatic Migration**: Schema changes trigger version increments
- **Backward Compatibility**: Old versions remain accessible
- **Data Preservation**: Existing data never lost during migrations

### Cross-Backend Migration
- **MongoDB → SQLite**: Not supported (complexity reduction)
- **SQLite → MongoDB**: Automatic when schema becomes complex
- **Version Preservation**: All versions maintained regardless of backend

## Configuration

### Environment Variables
```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=etl_pipeline

# SQLite Configuration (automatic)
ETL_SQLITE_DB_PATH=./data/sqlite/etl_pipeline.db        # Legacy single-file fallback
ETL_SQLITE_BASE_DIR=./data/sqlite                       # Root folder for per-version DBs
```

### Connection Management
- **MongoDB**: Singleton connection pool
- **SQLite**: Per-operation connections with proper cleanup
- **Error Handling**: Graceful degradation on backend failures

## Monitoring & Health Checks

### Health Endpoints
- **MongoDB**: Connection validation and basic query test
- **SQLite**: File existence and basic SELECT test
- **Overall**: Combined status reporting

### Metrics Tracked
- **Storage Operations**: Insert/update/delete counts
- **Query Performance**: Execution times and result sizes
- **Schema Evolution**: Version change frequency
- **Backend Utilization**: Data distribution across backends

## Troubleshooting

### Common Issues

#### MongoDB Connection Failures
- **Symptom**: Uploads fail with connection errors
- **Solution**: Verify MongoDB URI and network connectivity
- **Fallback**: System continues with SQLite-only operation

#### SQLite File Permissions
- **Symptom**: Database write errors
- **Solution**: Check directory permissions for `./data/sqlite/`
- **Recovery**: Manual file permission correction

#### Schema Compatibility Conflicts
- **Symptom**: Data routed to wrong backend
- **Solution**: Review schema field types and routing logic
- **Prevention**: Test schema compatibility before production

### Performance Tuning

#### MongoDB Optimization
- **Indexing**: Ensure proper indexes on query fields
- **Connection Pool**: Adjust pool size based on load
- **Query Patterns**: Optimize for common access patterns

#### SQLite Optimization
- **VACUUM**: Periodic database maintenance
- **Indexing**: Strategic indexes for query performance
- **Batch Operations**: Use transactions for bulk inserts

This storage strategy ensures optimal performance, data integrity, and scalability while maintaining simplicity in operations and maintenance.</content>
<parameter name="filePath">/home/yeashu/projects/dynamic-etl-pipeline/docs/storage_strategy.md
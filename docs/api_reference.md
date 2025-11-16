# API Reference

This document provides comprehensive details about all available API endpoints, including request formats, response structures, and usage examples.

## Base URL

All endpoints are relative to the API base URL (default: `http://localhost:8000`).

## Authentication

No authentication is required for this API.

## Content Types

- **Request Body**: JSON for POST endpoints
- **File Uploads**: Multipart form data
- **Response**: JSON for all endpoints

---

## Endpoints

### 1. File Upload

Upload a file for processing through the ETL pipeline.

#### Endpoint
```
POST /upload
```

#### Request Format
**Content-Type**: `multipart/form-data`

**Form Fields**:
- `file` (required): The file to upload (`.txt` or `.md` extensions only)
- `source_id` (optional): Custom identifier for the data source. If not provided, auto-generated from filename
- `version` (optional): Force a specific schema version (positive integer)

#### Request Examples

**Basic Upload (auto-generated source_id)**:
```bash
curl -X POST \
  -F "file=@sample_data.md" \
  http://localhost:8000/upload
```

**Upload with Custom Source ID**:
```bash
curl -X POST \
  -F "file=@user_data.txt" \
  -F "source_id=user_profiles" \
  http://localhost:8000/upload
```

**Upload with Forced Version**:
```bash
curl -X POST \
  -F "file=@updated_data.md" \
  -F "source_id=user_profiles" \
  -F "version=2" \
  http://localhost:8000/upload
```

#### Response Format

**Success Response (200)**:
```json
{
  "status": "success",
  "source_id": "user_profiles",
  "file_id": "abc123-def456-ghi789",
  "schema_id": "user_profiles_v1_jkl012",
  "version": 1,
  "records_extracted": 150,
  "records_normalized": 145,
  "parsed_fragments_summary": {
    "json_fragments": 45,
    "kv_pairs": 100
  },
  "evidence": {
    "extraction": {"status": "success", "fragments_found": 145},
    "normalization": {"status": "success", "records_processed": 145},
    "schema_inference": {"status": "success", "fields_detected": 8, "compatible_dbs": ["mongodb", "sqlite"]},
    "storage": {"status": "success", "mongodb_records": 145, "sqlite_records": 0}
  },
  "schema_metadata": {
    "schema_id": "user_profiles_v1_jkl012",
    "source_id": "user_profiles",
    "version": 1,
    "fields": [
      {
        "name": "id",
        "type": "integer",
        "nullable": false,
        "example_value": 123,
        "confidence": 1.0
      },
      {
        "name": "name",
        "type": "string",
        "nullable": true,
        "example_value": "John Doe",
        "confidence": 0.95
      }
    ],
    "generated_at": "2025-11-16T10:30:00Z",
    "compatible_dbs": ["mongodb", "sqlite"],
    "record_count": 145,
    "extraction_stats": {
      "json_fragments": 45,
      "kv_pairs": 100,
      "total_processed": 145
    }
  }
}
```

**Duplicate Upload Response**:
```json
{
  "status": "noop",
  "source_id": "user_profiles",
  "file_id": "def456-ghi789-jkl012",
  "schema_id": "user_profiles_v1_jkl012",
  "version": 1,
  "records_extracted": 150,
  "records_normalized": 145,
  "parsed_fragments_summary": {
    "json_fragments": 45,
    "kv_pairs": 100
  }
}
```

**Empty File Response**:
```json
{
  "status": "empty",
  "source_id": "empty_file",
  "file_id": "ghi789-jkl012-mno345",
  "records_extracted": 0,
  "records_normalized": 0,
  "parsed_fragments_summary": {}
}
```

#### Error Responses

**400 Bad Request - Invalid File Type**:
```json
{
  "detail": "Unsupported file extension '.pdf'. Allowed: .md, .txt."
}
```

**400 Bad Request - Invalid Source ID**:
```json
{
  "detail": "source_id may only contain letters, numbers, underscores, hyphens, and periods."
}
```

---

### 2. Get Current Schema

Retrieve the current schema metadata for a data source.

#### Endpoint
```
GET /schema
```

#### Request Format
**Query Parameters**:
- `source_id` (required): The data source identifier

#### Request Examples

```bash
curl "http://localhost:8000/schema?source_id=user_profiles"
```

#### Response Format

**Success Response (200)**:
```json
{
  "schema_data": {
    "schema_id": "user_profiles_v2_pqr678",
    "source_id": "user_profiles",
    "version": 2,
    "fields": [
      {
        "name": "id",
        "type": "integer",
        "nullable": false,
        "example_value": 123,
        "confidence": 1.0
      },
      {
        "name": "name",
        "type": "string",
        "nullable": true,
        "example_value": "John Doe",
        "confidence": 0.95
      },
      {
        "name": "email",
        "type": "string",
        "nullable": true,
        "example_value": "john@example.com",
        "confidence": 0.9
      }
    ],
    "generated_at": "2025-11-16T11:00:00Z",
    "compatible_dbs": ["mongodb", "sqlite"],
    "record_count": 200,
    "extraction_stats": {
      "json_fragments": 60,
      "kv_pairs": 140,
      "total_processed": 200
    },
    "primary_key_candidates": ["id"],
    "migration_notes": "Added email field"
  },
  "compatible_dbs": ["mongodb", "sqlite"]
}
```

#### Error Responses

**404 Not Found - Source Not Found**:
```json
{
  "detail": "No schema found for source 'nonexistent_source'"
}
```

---

### 3. Get Schema History

Retrieve the complete schema evolution history for a data source, including diffs between versions.

#### Endpoint
```
GET /schema/history
```

#### Request Format
**Query Parameters**:
- `source_id` (required): The data source identifier

#### Request Examples

```bash
curl "http://localhost:8000/schema/history?source_id=user_profiles"
```

#### Response Format

**Success Response (200)**:
```json
{
  "schemas": [
    {
      "schema_id": "user_profiles_v1_abc123",
      "source_id": "user_profiles",
      "version": 1,
      "fields": [
        {
          "name": "id",
          "type": "integer",
          "nullable": false
        },
        {
          "name": "name",
          "type": "string",
          "nullable": true
        }
      ],
      "generated_at": "2025-11-15T09:00:00Z",
      "compatible_dbs": ["mongodb", "sqlite"],
      "record_count": 100
    },
    {
      "schema_id": "user_profiles_v2_def456",
      "source_id": "user_profiles",
      "version": 2,
      "fields": [
        {
          "name": "id",
          "type": "integer",
          "nullable": false
        },
        {
          "name": "name",
          "type": "string",
          "nullable": true
        },
        {
          "name": "email",
          "type": "string",
          "nullable": true
        }
      ],
      "generated_at": "2025-11-16T11:00:00Z",
      "compatible_dbs": ["mongodb", "sqlite"],
      "record_count": 200,
      "migration_notes": "Added email field"
    }
  ],
  "diffs": [
    {
      "added_fields": ["email"],
      "removed_fields": [],
      "type_changes": {},
      "migration_notes": "Added email field to user profiles schema"
    }
  ]
}
```

#### Error Responses

**404 Not Found - Source Not Found**:
```json
{
  "detail": "No schema history found for source 'nonexistent_source'"
}
```

---

### 4. Execute Query

Execute a structured query against stored data.

#### Endpoint
```
POST /query
```

#### Request Format
**Content-Type**: `application/json`

**Query Parameters**:
- `source_id` (required): The data source identifier

**Request Body**: Structured query object (MongoDB-style syntax)

#### Query Structure

**MongoDB Queries (Default)**:
```json
{
  "filter": {
    "field_name": {"$operator": "value"}
  },
  "limit": 100,
  "sort": [["field_name", 1]]
}
```

**SQLite Queries**:
```json
{
  "engine": "sqlite",
  "where": {
    "field_name": {"$operator": "value"}
  },
  "select": ["field1", "field2"],
  "order_by": [["field_name", "desc"]],
  "limit": 50
}
```

#### Supported Operators

**Comparison Operators**:
- `$eq`: Equal to
- `$ne`: Not equal to
- `$gt`: Greater than
- `$gte`: Greater than or equal
- `$lt`: Less than
- `$lte`: Less than or equal

**Array Operators**:
- `$in`: Value in array

**String Operators**:
- `$like`: SQL LIKE pattern matching

#### Request Examples

**Simple MongoDB Query**:
```bash
curl -X POST "http://localhost:8000/query?source_id=user_profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "name": {"$eq": "John Doe"}
    },
    "limit": 10
  }'
```

**Complex MongoDB Query**:
```bash
curl -X POST "http://localhost:8000/query?source_id=user_profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "age": {"$gte": 25, "$lt": 35},
      "status": {"$in": ["active", "pending"]}
    },
    "sort": [["name", 1]],
    "limit": 50
  }'
```

**SQLite Query**:
```bash
curl -X POST "http://localhost:8000/query?source_id=user_profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "engine": "sqlite",
    "where": {
      "score": {"$gte": 80}
    },
    "select": ["id", "name", "score"],
    "order_by": [["score", "desc"]],
    "limit": 20
  }'
```

#### Response Format

**Success Response (200)**:
```json
{
  "query": {
    "engine": "mongodb",
    "filter": {"name": {"$eq": "John Doe"}},
    "limit": 10
  },
  "results": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "id": 123,
      "name": "John Doe",
      "email": "john@example.com",
      "age": 30
    }
  ],
  "result_count": 1,
  "execution_time_ms": 45.67
}
```

**SQLite Query Response**:
```json
{
  "query": {
    "engine": "sqlite",
    "sql": "SELECT id, name, score FROM user_profiles_v2 WHERE score >= ? ORDER BY score DESC LIMIT ?",
    "select": ["id", "name", "score"],
    "where": {"score": {"$gte": 80}},
    "order_by": [["score", "desc"]],
    "limit": 20
  },
  "results": [
    {"id": 456, "name": "Jane Smith", "score": 95},
    {"id": 789, "name": "Bob Johnson", "score": 88}
  ],
  "result_count": 2,
  "execution_time_ms": 12.34
}
```

#### Error Responses

**400 Bad Request - Invalid Query**:
```json
{
  "detail": "Query payload must be a JSON object."
}
```

**400 Bad Request - Unsupported Engine**:
```json
{
  "detail": "engine must be either 'mongodb' or 'sqlite'."
}
```

**400 Bad Request - Natural Language Query**:
```json
{
  "detail": "Natural language or raw textual queries are not supported. Provide a structured dict payload."
}
```

**404 Not Found - Source Not Found**:
```json
{
  "detail": "No data found for source 'nonexistent_source'"
}
```

---

### 5. Get Query Results

Retrieve paginated results from a previously executed query.

#### Endpoint
```
GET /records
```

#### Request Format
**Query Parameters**:
- `source_id` (required): The data source identifier
- `query_id` (optional): ID from a previous query execution
- `limit` (optional): Number of records to return (1-1000, default: 100)

#### Request Examples

**Get Records with Query ID**:
```bash
curl "http://localhost:8000/records?source_id=user_profiles&query_id=abc123&limit=50"
```

**Get Records without Query ID**:
```bash
curl "http://localhost:8000/records?source_id=user_profiles&limit=25"
```

#### Response Format

**Success Response (200)**:
```json
{
  "count": 25,
  "records": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "id": 123,
      "name": "John Doe",
      "email": "john@example.com"
    },
    {
      "_id": "507f1f77bcf86cd799439012",
      "id": 124,
      "name": "Jane Smith",
      "email": "jane@example.com"
    }
  ],
  "source_id": "user_profiles"
}
```

#### Error Responses

**400 Bad Request - Missing Query ID**:
```json
{
  "detail": "query_id is required to fetch records."
}
```

**404 Not Found - Query Not Found**:
```json
{
  "detail": "Query results not found for query_id 'invalid_id'"
}
```

---

### 6. Health Check

Check the health status of the API and storage backends.

#### Endpoint
```
GET /health
```

#### Request Format
No request body or parameters required.

#### Request Examples

```bash
curl "http://localhost:8000/health"
```

#### Response Format

**Success Response (200)**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-16T12:00:00Z",
  "version": "0.1.0",
  "services": {
    "mongodb": {
      "status": "connected",
      "database": "etl_pipeline"
    },
    "sqlite": {
      "status": "available",
      "path": "./data/sqlite/etl_pipeline.db"
    }
  }
}
```

**Degraded Response (200)**:
```json
{
  "status": "degraded",
  "timestamp": "2025-11-16T12:00:00Z",
  "version": "0.1.0",
  "services": {
    "mongodb": {
      "status": "error",
      "error": "Connection timeout"
    },
    "sqlite": {
      "status": "available",
      "path": "./data/sqlite/etl_pipeline.db"
    }
  }
}
```

#### Error Responses

**503 Service Unavailable**:
```json
{
  "status": "unhealthy",
  "timestamp": "2025-11-16T12:00:00Z",
  "version": "0.1.0",
  "services": {
    "mongodb": {
      "status": "error",
      "error": "Connection failed"
    },
    "sqlite": {
      "status": "error",
      "error": "Database file not found"
    }
  }
}
```

---

## Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Human-readable error message"
}
```

## Rate Limiting

No rate limiting is currently implemented.

## Data Types

### Field Types
- `string`: Text data
- `integer`: Whole numbers
- `number`: Floating point numbers
- `boolean`: True/false values
- `object`: Nested JSON objects
- `array`: Arrays/lists
- `null`: Null/empty values

### Storage Backends
- **MongoDB**: Handles all data types, preserves complex nested structures
- **SQLite**: Handles flat schemas (string, integer, number, boolean, null)

## Validation Rules

### File Upload
- **Allowed extensions**: `.txt`, `.md`
- **Source ID**: 1-60 characters, letters, numbers, underscores, hyphens, periods only
- **Version**: Positive integer (if specified)

### Queries
- Must be structured JSON objects
- No natural language queries allowed
- Engine must be "mongodb" or "sqlite" (case insensitive)
- SQLite queries require source to be stored in SQLite

## Response Time Expectations

- **Upload**: 1-30 seconds (depends on file size and complexity)
- **Schema operations**: < 1 second
- **Queries**: 10ms - 5 seconds (depends on data size and complexity)
- **Health check**: < 100ms</content>
<parameter name="filePath">/home/yeashu/projects/dynamic-etl-pipeline/docs/api_reference.md
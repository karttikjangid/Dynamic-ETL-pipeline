# Design Philosophy & Workflow

This document outlines the core design principles, workflow philosophy, and architectural decisions that guide the ETL pipeline implementation.

## Core Principles

### 1. **Deterministic Behavior**
- **Same input → Same output**: Identical files produce identical results
- **Version stability**: Schema versions change only on structural differences
- **Predictable routing**: Data flows to consistent storage backends

### 2. **Data Integrity First**
- **No data loss**: All extracted fragments are preserved
- **Type safety**: Strong typing with confidence scoring
- **Validation**: Schema validation at storage boundaries

### 3. **Performance Optimization**
- **Lazy evaluation**: Process only when needed
- **Efficient storage**: Choose optimal backend per data type
- **Batch operations**: Minimize I/O overhead

### 4. **Maintainable Architecture**
- **Single responsibility**: Each module owns one concern
- **Dependency control**: Strict import boundaries
- **Testable design**: Clear interfaces and contracts

## Workflow Philosophy

### 1. **Extract First** - Parse Raw Files
**Goal**: Convert unstructured text into structured fragments
- **Input**: `.txt` and `.md` files with mixed content
- **Process**: Pattern recognition and fragment extraction
- **Output**: `ExtractedRecord[]` with confidence scores
- **Principle**: Capture everything, classify later

### 2. **Normalize Second** - Standardize Data
**Goal**: Clean and standardize extracted data
- **Input**: Raw extracted fragments
- **Process**: Type inference and data cleaning
- **Output**: `NormalizedRecord[]` with consistent formats
- **Principle**: Prepare data for schema inference

### 3. **Infer Third** - Generate Schemas
**Goal**: Understand data structure and types
- **Input**: Normalized records
- **Process**: Statistical analysis and type detection
- **Output**: `SchemaMetadata` with field definitions
- **Principle**: Learn from data, not assumptions

### 4. **Compare Fourth** - Check for Changes
**Goal**: Determine if schema has evolved
- **Input**: New and existing schemas
- **Process**: Signature comparison and diff generation
- **Output**: Version decision and change tracking
- **Principle**: Version only on meaningful changes

### 5. **Route Fifth** - Choose Storage Backend
**Goal**: Select optimal storage for data type
- **Input**: Schema compatibility analysis
- **Process**: Data structure evaluation
- **Output**: Backend assignment (MongoDB/SQLite)
- **Principle**: Match storage to data characteristics

### 6. **Store Sixth** - Persist with Validation
**Goal**: Save data with schema enforcement
- **Input**: Records and schema metadata
- **Process**: Backend-specific formatting and insertion
- **Output**: Persistent storage with indexes
- **Principle**: Validate at storage boundaries

## Design Decisions

### Why Hybrid Storage?

**Performance Optimization**:
- Tabular data performs better in relational databases (SQLite)
- Complex data requires document storage (MongoDB)
- Query patterns differ by data structure

**Flexibility**:
- MongoDB handles any data complexity
- SQLite provides ACID transactions and SQL queries
- Automatic routing based on data analysis

**Cost Efficiency**:
- Single SQLite file vs MongoDB deployment
- No server management for simple use cases
- Scalable architecture for growth

### Why Intelligent Versioning?

**Deterministic Evolution**:
- Versions increment only on actual schema changes
- Eliminates "version churn" from identical uploads
- Maintains clean evolution history

**Storage Efficiency**:
- Identical schemas reuse versions
- Prevents redundant data storage
- Optimizes backup and recovery

**Audit Trail**:
- Tracks meaningful structural changes
- Provides migration context
- Supports compliance requirements

### Why Dual Schema Generation?

**Performance vs Intelligence Trade-off**:

**Custom Inference (Primary)**:
- **Fast**: Optimized for ETL pipeline speed
- **Rich**: Confidence scores, examples, metadata
- **Control**: Custom logic for edge cases
- **Use Case**: Core pipeline operations

**Genson Schema (Secondary)**:
- **Smart**: Advanced comparison capabilities
- **Standard**: JSON Schema compliance
- **Deep**: Sophisticated diffing support
- **Use Case**: Versioning and evolution tracking

**Complementary Benefits**:
- Fast pipeline operation + intelligent versioning
- ETL optimization + standard interoperability
- Custom control + advanced analysis

## Architectural Patterns

### Module Boundaries

**Strict Dependency Rules**:
```
main.py → api → services → (extractors | normalizers | inference | storage)
```

**No Reverse Dependencies**: Lower modules never import from higher ones

**Shared Contracts**: Core models available everywhere via `core/` package

### Error Handling Strategy

**Layered Error Types**:
- **Domain Errors**: `SchemaInferenceError`, `QueryExecutionError`
- **Infrastructure Errors**: `StorageError`, `PipelineError`
- **API Errors**: HTTP status codes with descriptive messages

**Error Propagation**:
- **Catch and Convert**: Infrastructure errors become domain errors
- **Preserve Context**: Original exceptions chained for debugging
- **Graceful Degradation**: Continue operation when possible

### Testing Philosophy

**Test Pyramid**:
- **Unit Tests**: Individual functions and classes
- **Integration Tests**: Module interactions
- **End-to-End Tests**: Complete pipeline workflows
- **Smoke Tests**: Critical path validation

**Test Data Strategy**:
- **Synthetic Data**: Controlled test scenarios
- **Realistic Samples**: Representative of production data
- **Edge Cases**: Boundary conditions and error paths

## Performance Considerations

### Data Processing
- **Streaming**: Process large files without full memory load
- **Batching**: Group operations to minimize I/O
- **Caching**: Reuse expensive computations

### Query Optimization
- **Index Strategy**: Automatic indexing on schema fields
- **Query Planning**: Choose optimal execution path
- **Result Limiting**: Prevent memory exhaustion

### Storage Efficiency
- **Compression**: Automatic data compression where beneficial
- **Deduplication**: Schema reuse prevents redundancy
- **Partitioning**: Logical separation of data sources

## Scalability Design

### Horizontal Scaling
- **Stateless Services**: API can scale horizontally
- **Shared Storage**: MongoDB/SQLite as coordination points
- **Load Balancing**: Distribute processing across instances

### Vertical Scaling
- **Memory Management**: Streaming for large files
- **CPU Optimization**: Parallel processing where applicable
- **I/O Optimization**: Batch operations and connection pooling

### Data Volume Handling
- **Pagination**: Large result sets delivered in chunks
- **Archiving**: Old versions can be archived
- **Sampling**: Statistical analysis on large datasets

## Security Considerations

### Data Protection
- **Input Validation**: Strict file type and content checking
- **SQL Injection Prevention**: Parameterized queries only
- **Access Control**: API authentication when required

### Operational Security
- **Logging**: Sensitive data not logged
- **Error Messages**: No internal details exposed
- **File Handling**: Secure temporary file management

## Future Evolution

### Extension Points
- **New Extractors**: Plugin architecture for additional formats
- **Custom Normalizers**: Domain-specific data cleaning
- **Storage Backends**: Additional database support

### Migration Strategy
- **Backward Compatibility**: API contracts maintained
- **Data Migration**: Automatic schema evolution
- **Rolling Updates**: Zero-downtime deployments

### Monitoring & Observability
- **Metrics**: Performance and usage statistics
- **Health Checks**: System status monitoring
- **Tracing**: Request flow tracking

This design philosophy ensures the ETL pipeline remains maintainable, performant, and evolvable while meeting the core requirements of deterministic data processing and intelligent storage management.</content>
<parameter name="filePath">/home/yeashu/projects/dynamic-etl-pipeline/docs/design_philosophy.md
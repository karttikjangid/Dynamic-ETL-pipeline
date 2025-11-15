# Storage Module Notes

## Implemented

- Mongo connection singleton (`MongoConnection`)
- Collection management helpers (validation schema, indexes, add-field routine)
- Document insertion utilities with schema-aware validation
- Document retrieval helpers (list, count, by id)
- Schema persistence store for schema metadata history
- Schema migration utilities with diffing

## Deferred / Future Work

- Backward-compatible schema migrations (preserve old query behavior)
- Rich type coercion during schema evolution
- Advanced index strategy (TTL, compound, partial)
- Schema validation against optional stricter rules

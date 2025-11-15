"""Custom exception hierarchy for pipeline errors."""


class PipelineError(Exception):
    """Base application error."""


class ExtractionError(PipelineError):
    """Raised when record extraction fails."""


class NormalizationError(PipelineError):
    """Raised when normalization cannot produce valid records."""


class SchemaInferenceError(PipelineError):
    """Raised when schema inference encounters an unrecoverable problem."""


class StorageError(PipelineError):
    """Raised when database operations fail."""


class QueryExecutionError(PipelineError):
    """Raised when executing a strict query fails."""

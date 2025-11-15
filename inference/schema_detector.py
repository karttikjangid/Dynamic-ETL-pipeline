"""Schema detection utilities."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import pyarrow as pa


def detect_data_types(records: List[Dict]) -> Dict[str, str]:
    """Infer data types from normalized records."""

    raise NotImplementedError


def load_records_to_dataframe(records: List[Dict]) -> pd.DataFrame:
    """Load records into a pandas DataFrame for analysis."""

    raise NotImplementedError


def infer_arrow_schema(df: pd.DataFrame) -> pa.Schema:
    """Use Arrow to stabilize inferred schema."""

    raise NotImplementedError


def extract_field_types(arrow_schema: pa.Schema) -> Dict[str, str]:
    """Convert Arrow schema to simple type mapping."""

    raise NotImplementedError

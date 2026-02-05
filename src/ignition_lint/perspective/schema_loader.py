"""Helpers for loading perspective component schemas."""
from __future__ import annotations

from typing import Dict

from ..schemas import schema_path_for
import json


def load_schema(mode: str = "robust") -> Dict:
    """Load a schema variant by mode name."""
    schema_path = schema_path_for(mode)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

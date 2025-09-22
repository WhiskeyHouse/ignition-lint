"""Helpers for loading perspective component schemas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

SCHEMA_FILES = {
    "strict": "core-ia-components-schema.json",
    "robust": "core-ia-components-schema-robust.json",
    "permissive": "core-ia-components-schema-permissive.json",
}


def load_schema(schema_dir: Path, mode: str = "robust") -> Dict:
    """Load a schema variant from the schemas directory."""
    normalized = mode.lower()
    if normalized not in SCHEMA_FILES:
        raise ValueError(f"Unknown schema mode '{mode}'. Options: {', '.join(SCHEMA_FILES)}")

    schema_path = schema_dir / SCHEMA_FILES[normalized]
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

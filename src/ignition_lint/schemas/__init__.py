"""Canonical schema path resolution for ignition-lint."""

from __future__ import annotations

from pathlib import Path

SCHEMA_FILES = {
    "strict": "core-ia-components-schema.json",
    "robust": "core-ia-components-schema-robust.json",
    "permissive": "core-ia-components-schema-permissive.json",
}

TAG_SCHEMA_FILES = {
    "robust": "tag-schema-robust.json",
}

_SCHEMA_DIR = Path(__file__).parent


def schema_path_for(mode: str) -> Path:
    """Return the absolute path to the Perspective schema file for the given mode."""
    normalized = mode.lower()
    if normalized not in SCHEMA_FILES:
        raise ValueError(
            f"Unknown schema mode '{mode}'. Options: {', '.join(SCHEMA_FILES)}"
        )
    return _SCHEMA_DIR / SCHEMA_FILES[normalized]


def tag_schema_path_for(mode: str) -> Path:
    """Return the absolute path to the tag schema file for the given mode."""
    normalized = mode.lower()
    if normalized not in TAG_SCHEMA_FILES:
        raise ValueError(
            f"Unknown tag schema mode '{mode}'. Options: {', '.join(TAG_SCHEMA_FILES)}"
        )
    return _SCHEMA_DIR / TAG_SCHEMA_FILES[normalized]

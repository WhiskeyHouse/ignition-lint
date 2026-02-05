"""Tests for schema path resolution from within the installed package."""

import pytest

from ignition_lint.schemas import schema_path_for


@pytest.mark.parametrize("mode", ["strict", "robust", "permissive"])
def test_schema_path_exists(mode):
    path = schema_path_for(mode)
    assert path.exists(), f"Schema file missing for mode '{mode}': {path}"


@pytest.mark.parametrize("mode", ["strict", "robust", "permissive"])
def test_schema_path_is_json(mode):
    path = schema_path_for(mode)
    assert path.suffix == ".json"


def test_invalid_mode_raises():
    with pytest.raises(ValueError, match="Unknown schema mode"):
        schema_path_for("nonexistent")

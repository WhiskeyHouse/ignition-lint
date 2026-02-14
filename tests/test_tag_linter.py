"""Tests for IgnitionTagLinter — tag/UDT JSON structural validation."""

import json
import os
import tempfile

import pytest

from ignition_lint.schemas import tag_schema_path_for
from ignition_lint.tags import IgnitionTagLinter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lint_tag(tag_data):
    """Write tag_data to a temp JSON file and lint it."""
    linter = IgnitionTagLinter()
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "tags.json")
    with open(path, "w") as f:
        json.dump(tag_data, f)

    try:
        linter.lint_file(path)
    finally:
        os.unlink(path)
        os.rmdir(tmpdir)

    return linter.issues


def _codes(issues):
    """Extract the set of issue codes."""
    return {i.code for i in issues}


def _issues_with_code(issues, code):
    """Filter issues by code."""
    return [i for i in issues if i.code == code]


# ---------------------------------------------------------------------------
# TestTagTypeValidation
# ---------------------------------------------------------------------------


class TestTagTypeValidation:
    def test_valid_atomic_tag(self):
        tag = {
            "name": "MyTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "memory",
        }
        issues = _lint_tag(tag)
        assert "INVALID_TAG_TYPE" not in _codes(issues)
        assert "MISSING_TAG_NAME" not in _codes(issues)

    def test_valid_folder(self):
        tag = {"name": "Folder1", "tagType": "Folder", "tags": []}
        issues = _lint_tag(tag)
        assert "INVALID_TAG_TYPE" not in _codes(issues)

    def test_valid_udt_type(self):
        tag = {
            "name": "MyUDT",
            "tagType": "UdtType",
            "typeId": "custom/MyUDT",
            "tags": [],
        }
        issues = _lint_tag(tag)
        assert "INVALID_TAG_TYPE" not in _codes(issues)

    def test_valid_udt_instance(self):
        tag = {"name": "Inst1", "tagType": "UdtInstance", "typeId": "custom/MyUDT"}
        issues = _lint_tag(tag)
        assert "INVALID_TAG_TYPE" not in _codes(issues)
        assert "MISSING_TYPE_ID" not in _codes(issues)

    def test_invalid_tag_type(self):
        tag = {"name": "Bad", "tagType": "InvalidType"}
        issues = _lint_tag(tag)
        assert "INVALID_TAG_TYPE" in _codes(issues)

    def test_missing_name_info_severity(self):
        """Missing name is INFO (not ERROR) since git module uses filename as name."""
        tag = {"tagType": "AtomicTag", "dataType": "Int4"}
        issues = _lint_tag(tag)
        assert "MISSING_TAG_NAME" in _codes(issues)
        name_issues = _issues_with_code(issues, "MISSING_TAG_NAME")
        from ignition_lint.reporting import LintSeverity

        assert all(i.severity == LintSeverity.INFO for i in name_issues)

    def test_file_per_tag_udt_no_errors(self):
        """UdtType without root name (file-per-tag format) should not produce errors."""
        tag = {
            "tagType": "UdtType",
            "tags": [
                {
                    "name": "token",
                    "tagType": "AtomicTag",
                    "dataType": "String",
                    "valueSource": "memory",
                },
            ],
        }
        issues = _lint_tag(tag)
        errors = [i for i in issues if i.severity.value == "error"]
        assert errors == []


# ---------------------------------------------------------------------------
# TestAtomicTagValidation
# ---------------------------------------------------------------------------


class TestAtomicTagValidation:
    def test_missing_data_type(self):
        tag = {"name": "NoData", "tagType": "AtomicTag", "valueSource": "memory"}
        issues = _lint_tag(tag)
        assert "MISSING_DATA_TYPE" in _codes(issues)

    def test_missing_value_source(self):
        tag = {"name": "NoVS", "tagType": "AtomicTag", "dataType": "Int4"}
        issues = _lint_tag(tag)
        assert "MISSING_VALUE_SOURCE" in _codes(issues)

    def test_complete_tag_no_missing_warnings(self):
        tag = {
            "name": "Complete",
            "tagType": "AtomicTag",
            "dataType": "Float8",
            "valueSource": "memory",
            "value": 3.14,
        }
        issues = _lint_tag(tag)
        assert "MISSING_DATA_TYPE" not in _codes(issues)
        assert "MISSING_VALUE_SOURCE" not in _codes(issues)

    def test_opc_missing_config(self):
        tag = {
            "name": "OpcTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "opc",
        }
        issues = _lint_tag(tag)
        assert "OPC_MISSING_CONFIG" in _codes(issues)

    def test_opc_with_config_no_warning(self):
        tag = {
            "name": "OpcTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "opc",
            "opcServer": "Ignition OPC UA Server",
            "opcItemPath": "ns=1;s=Channel1.Device1.Tag1",
        }
        issues = _lint_tag(tag)
        assert "OPC_MISSING_CONFIG" not in _codes(issues)

    def test_expr_missing_expression(self):
        tag = {
            "name": "ExprTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "expr",
        }
        issues = _lint_tag(tag)
        assert "EXPR_MISSING_EXPRESSION" in _codes(issues)

    def test_expr_with_expression_no_error(self):
        tag = {
            "name": "ExprTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "expr",
            "expression": "{[default]Path/To/Tag} + 1",
        }
        issues = _lint_tag(tag)
        assert "EXPR_MISSING_EXPRESSION" not in _codes(issues)

    def test_db_missing_query(self):
        tag = {
            "name": "DbTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "db",
        }
        issues = _lint_tag(tag)
        assert "DB_MISSING_QUERY" in _codes(issues)

    def test_unknown_prop_flagged(self):
        tag = {
            "name": "Typo",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "memory",
            "taqGroup": "Default",  # typo: should be tagGroup
        }
        issues = _lint_tag(tag)
        assert "UNKNOWN_TAG_PROP" in _codes(issues)
        unknown_issues = _issues_with_code(issues, "UNKNOWN_TAG_PROP")
        assert any("taqGroup" in i.message for i in unknown_issues)

    def test_binding_object_not_flagged(self):
        """Binding objects (dict with bindType) should not trigger UNKNOWN_TAG_PROP."""
        tag = {
            "name": "BoundTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "memory",
            "customProp": {
                "bindType": "property",
                "binding": "[default]some/path",
                "value": 0,
            },
        }
        issues = _lint_tag(tag)
        unknown = _issues_with_code(issues, "UNKNOWN_TAG_PROP")
        assert not any("customProp" in i.message for i in unknown)


# ---------------------------------------------------------------------------
# TestUdtValidation
# ---------------------------------------------------------------------------


class TestUdtValidation:
    def test_udt_instance_missing_type_id(self):
        tag = {"name": "NoType", "tagType": "UdtInstance"}
        issues = _lint_tag(tag)
        assert "MISSING_TYPE_ID" in _codes(issues)

    def test_udt_instance_with_type_id(self):
        tag = {"name": "HasType", "tagType": "UdtInstance", "typeId": "custom/MyUDT"}
        issues = _lint_tag(tag)
        assert "MISSING_TYPE_ID" not in _codes(issues)

    def test_udt_type_custom_param_fields_not_flagged(self):
        """UdtType should NOT get UNKNOWN_TAG_PROP for custom parameter fields."""
        tag = {
            "name": "MyUDT",
            "tagType": "UdtType",
            "typeId": "custom/MyUDT",
            "parameters": {"Prefix": {"dataType": "String", "value": ""}},
            "customField": "some value",
        }
        issues = _lint_tag(tag)
        assert "UNKNOWN_TAG_PROP" not in _codes(issues)


# ---------------------------------------------------------------------------
# TestEventScriptValidation
# ---------------------------------------------------------------------------


class TestEventScriptValidation:
    def test_dict_format_valid_script(self):
        tag = {
            "name": "ScriptTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "memory",
            "eventScripts": {
                "valueChanged": {
                    "eventScript": "x = 1\n",
                    "enabled": True,
                }
            },
        }
        issues = _lint_tag(tag)
        assert "JYTHON_SYNTAX_ERROR" not in _codes(issues)

    def test_array_format_valid_script(self):
        tag = {
            "name": "ArrayScript",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "memory",
            "eventScripts": [
                {"eventid": "valueChanged", "script": "y = 2\n", "enabled": True}
            ],
        }
        issues = _lint_tag(tag)
        assert "JYTHON_SYNTAX_ERROR" not in _codes(issues)

    def test_empty_scripts_skipped(self):
        tag = {
            "name": "EmptyScript",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "memory",
            "eventScripts": {"valueChanged": {"eventScript": "", "enabled": False}},
        }
        issues = _lint_tag(tag)
        # No script issues — script was empty
        script_issues = [i for i in issues if "JYTHON" in i.code or "SYNTAX" in i.code]
        assert script_issues == []


# ---------------------------------------------------------------------------
# TestNestedTags
# ---------------------------------------------------------------------------


class TestNestedTags:
    def test_folder_children_validated(self):
        tag = {
            "name": "Folder",
            "tagType": "Folder",
            "tags": [
                {"name": "Child", "tagType": "AtomicTag"},
            ],
        }
        issues = _lint_tag(tag)
        # Child should get MISSING_DATA_TYPE
        assert "MISSING_DATA_TYPE" in _codes(issues)

    def test_deep_nesting(self):
        tag = {
            "name": "L1",
            "tagType": "Folder",
            "tags": [
                {
                    "name": "L2",
                    "tagType": "Folder",
                    "tags": [
                        {
                            "name": "L3",
                            "tagType": "AtomicTag",
                            "dataType": "Boolean",
                            "valueSource": "expr",
                        }
                    ],
                }
            ],
        }
        issues = _lint_tag(tag)
        # L3 is expr but no expression
        assert "EXPR_MISSING_EXPRESSION" in _codes(issues)
        expr_issues = _issues_with_code(issues, "EXPR_MISSING_EXPRESSION")
        assert any("L3" in i.component_path for i in expr_issues)


# ---------------------------------------------------------------------------
# TestHistoryValidation
# ---------------------------------------------------------------------------


class TestHistoryValidation:
    def test_history_no_provider(self):
        tag = {
            "name": "HistTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "memory",
            "historyEnabled": True,
        }
        issues = _lint_tag(tag)
        assert "HISTORY_NO_PROVIDER" in _codes(issues)

    def test_history_with_provider(self):
        tag = {
            "name": "HistTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "memory",
            "historyEnabled": True,
            "historyProvider": "default",
        }
        issues = _lint_tag(tag)
        assert "HISTORY_NO_PROVIDER" not in _codes(issues)


# ---------------------------------------------------------------------------
# TestSchemaResolution
# ---------------------------------------------------------------------------


class TestSchemaResolution:
    def test_tag_schema_file_exists(self):
        path = tag_schema_path_for("robust")
        assert path.exists(), f"Tag schema file missing: {path}"

    def test_tag_schema_is_json(self):
        path = tag_schema_path_for("robust")
        assert path.suffix == ".json"

    def test_invalid_tag_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown tag schema mode"):
            tag_schema_path_for("nonexistent")

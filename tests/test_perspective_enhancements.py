"""Tests for Perspective linter enhancements (onChange, unused props, expressions)."""

import json
import os
import tempfile

from ignition_lint.perspective.linter import IgnitionPerspectiveLinter


def _lint_view(view_data):
    """Helper: write view_data to a temp dir/view.json and lint it."""
    linter = IgnitionPerspectiveLinter()
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "view.json")
    with open(path, "w") as f:
        json.dump(view_data, f)

    try:
        linter.lint_file(path)
    finally:
        os.unlink(path)
        os.rmdir(tmpdir)

    return linter.issues


def _codes(issues):
    return {i.code for i in issues}


class TestOnChangeValidation:
    def test_valid_onchange_script(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "onChange": {
                            "script": "\tvalue = self.props.text\n\tsystem.perspective.print(str(value))"
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        # No syntax errors expected
        assert "JYTHON_SYNTAX_ERROR" not in _codes(issues)

    def test_onchange_syntax_error(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [],
                "propConfig": {
                    "props.text": {"onChange": {"script": "\tif value >\n\t\tpass"}}
                },
            },
        }
        issues = _lint_view(view)
        assert "JYTHON_SYNTAX_ERROR" in _codes(issues)

    def test_view_level_onchange(self):
        view = {
            "custom": {},
            "propConfig": {
                "custom.myProp": {"onChange": {"script": "\tif value >\n\t\tpass"}}
            },
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "JYTHON_SYNTAX_ERROR" in _codes(issues)


class TestUnusedProperties:
    def test_unused_custom_flagged(self):
        view = {
            "custom": {"unusedProp": ""},
            "params": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "UNUSED_CUSTOM_PROPERTY" in _codes(issues)

    def test_used_in_expression_passes(self):
        view = {
            "custom": {"myProp": ""},
            "params": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "MyLabel"},
                        "props": {},
                        "propConfig": {
                            "props.text": {
                                "binding": {
                                    "type": "expr",
                                    "config": {"expression": "{view.custom.myProp}"},
                                }
                            }
                        },
                    }
                ],
            },
        }
        issues = _lint_view(view)
        assert "UNUSED_CUSTOM_PROPERTY" not in _codes(issues)

    def test_used_in_propconfig_key_passes(self):
        view = {
            "custom": {"myProp": ""},
            "params": {},
            "propConfig": {
                "custom.myProp": {
                    "binding": {
                        "type": "tag",
                        "config": {"tagPath": "[default]MyTag"},
                    }
                }
            },
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "UNUSED_CUSTOM_PROPERTY" not in _codes(issues)

    def test_unused_param_info(self):
        view = {
            "custom": {},
            "params": {"unusedParam": "default"},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "UNUSED_PARAM_PROPERTY" in _codes(issues)
        param_issues = [i for i in issues if i.code == "UNUSED_PARAM_PROPERTY"]
        from ignition_lint.reporting import LintSeverity

        assert all(i.severity == LintSeverity.INFO for i in param_issues)


class TestUnknownPropValidation:
    def test_unknown_prop_flagged(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "MyLabel"},
                "props": {"text": "Hello", "random": True},
                "children": [],
            },
        }
        issues = _lint_view(view)
        unknown = [i for i in issues if i.code == "UNKNOWN_PROP"]
        assert len(unknown) == 1
        assert "random" in unknown[0].message

    def test_known_props_not_flagged(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "MyLabel"},
                "props": {"text": "Hello", "style": {"color": "red"}, "visible": True},
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "UNKNOWN_PROP" not in _codes(issues)

    def test_unknown_prop_severity_is_style(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "props": {"bogus": 42},
                "children": [],
            },
        }
        issues = _lint_view(view)
        unknown = [i for i in issues if i.code == "UNKNOWN_PROP"]
        from ignition_lint.reporting import LintSeverity

        assert all(i.severity == LintSeverity.STYLE for i in unknown)

    def test_multiple_unknown_props(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "props": {"foo": 1, "xyzzy": 2, "direction": "row"},
                "children": [],
            },
        }
        issues = _lint_view(view)
        unknown = [i for i in issues if i.code == "UNKNOWN_PROP"]
        assert len(unknown) == 2
        flagged_names = {i.message.split("'")[1] for i in unknown}
        assert flagged_names == {"foo", "xyzzy"}

    def test_empty_props_safe(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "props": {},
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "UNKNOWN_PROP" not in _codes(issues)

    def test_no_props_key_safe(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "UNKNOWN_PROP" not in _codes(issues)

    def test_image_fit_prop_not_flagged(self):
        """Regression: 'fit' is a valid prop for ia.display.image."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.display.image",
                "meta": {"name": "MyImage"},
                "props": {
                    "source": "/images/logo.png",
                    "fit": {"mode": "contain"},
                    "alt": "Logo",
                },
            },
        }
        issues = _lint_view(view)
        assert "UNKNOWN_PROP" not in _codes(issues)

    def test_known_props_from_schema(self):
        """Known prop names are derived from the component schema, not hardcoded."""
        linter = IgnitionPerspectiveLinter()
        # These should all be in the schema's props.properties
        assert "fit" in linter.known_prop_names
        assert "tagPath" in linter.known_prop_names
        assert "viewPath" in linter.known_prop_names
        assert "style" in linter.known_prop_names
        assert "text" in linter.known_prop_names


class TestPerComponentUnknownProp:
    """Per-component property map reduces UNKNOWN_PROP false positives."""

    def test_table_specific_props_not_flagged(self):
        """Table-specific props like 'columns', 'data', 'pager' should not be flagged."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.display.table",
                "meta": {"name": "DataTable"},
                "props": {
                    "data": [],
                    "columns": [],
                    "pager": {"show": True},
                    "filter": {"enabled": True},
                    "style": {},
                },
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "UNKNOWN_PROP" not in _codes(issues)

    def test_genuinely_unknown_prop_still_flagged(self):
        """A truly unknown prop should still be flagged even on a known component."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.display.table",
                "meta": {"name": "DataTable"},
                "props": {"data": [], "zzNonexistent": True},
                "children": [],
            },
        }
        issues = _lint_view(view)
        unknown = [i for i in issues if i.code == "UNKNOWN_PROP"]
        assert len(unknown) == 1
        assert "zzNonexistent" in unknown[0].message

    def test_dropdown_specific_props_not_flagged(self):
        """Dropdown-specific props should pass validation."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.input.dropdown",
                "meta": {"name": "MyDropdown"},
                "props": {
                    "options": [],
                    "value": "",
                    "multiSelect": False,
                    "showClearIcon": True,
                },
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "UNKNOWN_PROP" not in _codes(issues)

    def test_unknown_component_type_falls_back_to_generic(self):
        """Unknown component types still use generic schema props."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.custom.mywidget",
                "meta": {"name": "Widget"},
                "props": {"style": {}, "text": "hello"},
                "children": [],
            },
        }
        issues = _lint_view(view)
        assert "UNKNOWN_PROP" not in _codes(issues)


class TestExpressionValidation:
    def test_now_default_polling_flagged(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "TimeLabel"},
                "props": {},
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "expr",
                            "config": {"expression": "dateFormat(now(), 'HH:mm:ss')"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "EXPR_NOW_DEFAULT_POLLING" in _codes(issues)

    def test_expression_transform_validated(self):
        view = {
            "custom": {},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "props": {},
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "tag",
                            "config": {"tagPath": "[default]MyTag"},
                            "transforms": [
                                {
                                    "type": "expression",
                                    "expression": "getSibling(0, 'Other').props.value",
                                }
                            ],
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "EXPR_BAD_COMPONENT_REF" in _codes(issues)


class TestPropertyBindingPathValidation:
    def test_root_dot_custom_flagged(self):
        """Property binding with /root.custom.X should be view.custom.X."""
        view = {
            "custom": {"auditData": {}},
            "root": {
                "type": "ia.display.table",
                "meta": {"name": "AuditTable"},
                "children": [],
                "propConfig": {
                    "props.data": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "/root.custom.auditData"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        codes = _codes(issues)
        assert "BINDING_ROOT_DOT_PATH" in codes
        # Check the suggestion is explicit about the fix
        issue = next(i for i in issues if i.code == "BINDING_ROOT_DOT_PATH")
        assert "view.custom.auditData" in issue.suggestion
        assert '"path": "view.custom.auditData"' in issue.suggestion

    def test_root_dot_params_flagged(self):
        """Property binding with /root.params.X should be view.params.X."""
        view = {
            "custom": {},
            "params": {"item": {}},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "/root.params.item"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_ROOT_DOT_PATH" in _codes(issues)

    def test_root_slash_component_ref_not_flagged(self):
        """Absolute component refs with /root/ (slashes) are valid."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "MyLabel"},
                        "children": [],
                        "propConfig": {
                            "props.text": {
                                "binding": {
                                    "type": "property",
                                    "config": {
                                        "path": "/root/Header/Label.props.text"
                                    },
                                }
                            }
                        },
                    }
                ],
            },
        }
        issues = _lint_view(view)
        assert "BINDING_ROOT_DOT_PATH" not in _codes(issues)

    def test_view_custom_path_not_flagged(self):
        """Correct view.custom.X paths should not be flagged."""
        view = {
            "custom": {"auditData": {}},
            "root": {
                "type": "ia.display.table",
                "meta": {"name": "AuditTable"},
                "children": [],
                "propConfig": {
                    "props.data": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "view.custom.auditData"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_ROOT_DOT_PATH" not in _codes(issues)

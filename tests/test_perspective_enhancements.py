"""Tests for Perspective linter enhancements (onChange, unused props, expressions)."""
import json
import os
import tempfile

import pytest

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
                    "props.text": {
                        "onChange": {
                            "script": "\tif value >\n\t\tpass"
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "JYTHON_SYNTAX_ERROR" in _codes(issues)

    def test_view_level_onchange(self):
        view = {
            "custom": {},
            "propConfig": {
                "custom.myProp": {
                    "onChange": {
                        "script": "\tif value >\n\t\tpass"
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
                                    "config": {
                                        "expression": "{view.custom.myProp}"
                                    },
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

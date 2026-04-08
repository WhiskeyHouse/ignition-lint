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
                                    "config": {"path": "/root/Header/Label.props.text"},
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


class TestBindingPathSyntax:
    """Tier 1: Syntax validation for property binding paths."""

    def test_bare_root_custom_flagged(self):
        """root.custom.X without leading / or view. scope is flagged."""
        view = {
            "custom": {"myProp": ""},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "root.custom.myProp"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_BARE_ROOT_PATH" in _codes(issues)
        issue = next(i for i in issues if i.code == "BINDING_BARE_ROOT_PATH")
        assert "view.custom.myProp" in issue.suggestion

    def test_bare_root_params_flagged(self):
        """root.params.X without leading / or view. scope is flagged."""
        view = {
            "custom": {},
            "params": {"item": ""},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "root.params.item"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_BARE_ROOT_PATH" in _codes(issues)

    def test_invalid_scope_flagged(self):
        """A path with dots but no recognized scope prefix is flagged."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "foo.bar.baz"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_INVALID_SCOPE" in _codes(issues)
        issue = next(i for i in issues if i.code == "BINDING_INVALID_SCOPE")
        assert "Valid scopes" in issue.suggestion

    def test_valid_scopes_not_flagged(self):
        """view., this., session., page., parent. scopes should pass."""
        for scope in [
            "view.custom.x",
            "this.props.text",
            "session.props.auth",
            "page.props.path",
            "parent.custom.y",
        ]:
            view = {
                "custom": {"x": ""},
                "root": {
                    "type": "ia.display.label",
                    "meta": {"name": "Label"},
                    "children": [],
                    "propConfig": {
                        "props.text": {
                            "binding": {
                                "type": "property",
                                "config": {"path": scope},
                            }
                        }
                    },
                },
            }
            issues = _lint_view(view)
            scope_codes = {"BINDING_BARE_ROOT_PATH", "BINDING_INVALID_SCOPE"}
            assert not scope_codes & _codes(issues), (
                f"Scope '{scope}' was incorrectly flagged"
            )

    def test_relative_path_not_flagged(self):
        """Relative component refs (./ and ../) should pass syntax checks."""
        for path in ["./Sibling.props.text", "../Parent/Other.props.value"]:
            view = {
                "custom": {},
                "root": {
                    "type": "ia.display.label",
                    "meta": {"name": "Label"},
                    "children": [],
                    "propConfig": {
                        "props.text": {
                            "binding": {
                                "type": "property",
                                "config": {"path": path},
                            }
                        }
                    },
                },
            }
            issues = _lint_view(view)
            syntax_codes = {"BINDING_BARE_ROOT_PATH", "BINDING_INVALID_SCOPE"}
            assert not syntax_codes & _codes(issues), (
                f"Path '{path}' was incorrectly flagged"
            )

    def test_no_duplicate_for_root_dot(self):
        """BINDING_ROOT_DOT_PATH should not also trigger BINDING_INVALID_SCOPE."""
        view = {
            "custom": {"x": ""},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "/root.custom.x"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_ROOT_DOT_PATH" in _codes(issues)
        assert "BINDING_INVALID_SCOPE" not in _codes(issues)
        assert "BINDING_BARE_ROOT_PATH" not in _codes(issues)


class TestBindingPathResolution:
    """Tier 2: Verify view.custom.X and view.params.X resolve."""

    def test_binding_view_custom_not_found(self):
        """Property binding to view.custom.X where X doesn't exist."""
        view = {
            "custom": {"realProp": ""},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "view.custom.missingProp"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_VIEW_PROP_NOT_FOUND" in _codes(issues)
        issue = next(i for i in issues if i.code == "BINDING_VIEW_PROP_NOT_FOUND")
        assert "missingProp" in issue.message

    def test_binding_view_params_not_found(self):
        """Property binding to view.params.X where X doesn't exist."""
        view = {
            "custom": {},
            "params": {"realParam": ""},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "view.params.missingParam"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_VIEW_PROP_NOT_FOUND" in _codes(issues)

    def test_binding_view_custom_found(self):
        """Property binding to view.custom.X where X exists should pass."""
        view = {
            "custom": {"myProp": "hello"},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "view.custom.myProp"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_VIEW_PROP_NOT_FOUND" not in _codes(issues)

    def test_binding_deep_path_checks_top_key_only(self):
        """view.custom.alarm.name only checks that 'alarm' exists, not 'alarm.name'."""
        view = {
            "custom": {"alarm": {"name": "Test"}},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "view.custom.alarm.name"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_VIEW_PROP_NOT_FOUND" not in _codes(issues)

    def test_binding_array_index_stripped(self):
        """view.custom.items[0].x checks that 'items' exists."""
        view = {
            "custom": {"items": [1, 2, 3]},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "property",
                            "config": {"path": "view.custom.items[0].x"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "BINDING_VIEW_PROP_NOT_FOUND" not in _codes(issues)


class TestComponentPathResolution:
    """Tier 3: Verify /root/A/B component paths resolve."""

    def test_valid_component_path_passes(self):
        """A valid /root/Header/Label.props.text path should not be flagged."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.container.flex",
                        "meta": {"name": "Header"},
                        "children": [
                            {
                                "type": "ia.display.label",
                                "meta": {"name": "Label"},
                                "children": [],
                            }
                        ],
                    },
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "Consumer"},
                        "children": [],
                        "propConfig": {
                            "props.text": {
                                "binding": {
                                    "type": "property",
                                    "config": {"path": "/root/Header/Label.props.text"},
                                }
                            }
                        },
                    },
                ],
            },
        }
        issues = _lint_view(view)
        assert "BINDING_COMPONENT_NOT_FOUND" not in _codes(issues)

    def test_invalid_component_path_flagged(self):
        """A /root/Header/Missing.props.text path should be flagged."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.container.flex",
                        "meta": {"name": "Header"},
                        "children": [
                            {
                                "type": "ia.display.label",
                                "meta": {"name": "Label"},
                                "children": [],
                            }
                        ],
                    },
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "Consumer"},
                        "children": [],
                        "propConfig": {
                            "props.text": {
                                "binding": {
                                    "type": "property",
                                    "config": {
                                        "path": "/root/Header/Missing.props.text"
                                    },
                                }
                            }
                        },
                    },
                ],
            },
        }
        issues = _lint_view(view)
        assert "BINDING_COMPONENT_NOT_FOUND" in _codes(issues)
        issue = next(i for i in issues if i.code == "BINDING_COMPONENT_NOT_FOUND")
        assert "Missing" in issue.message
        assert "Label" in issue.suggestion  # Should suggest available children

    def test_invalid_first_segment_flagged(self):
        """A /root/Nonexistent.props.text path with wrong first child."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "Actual"},
                        "children": [],
                        "propConfig": {
                            "props.text": {
                                "binding": {
                                    "type": "property",
                                    "config": {"path": "/root/Nonexistent.props.text"},
                                }
                            }
                        },
                    }
                ],
            },
        }
        issues = _lint_view(view)
        assert "BINDING_COMPONENT_NOT_FOUND" in _codes(issues)
        issue = next(i for i in issues if i.code == "BINDING_COMPONENT_NOT_FOUND")
        assert "Actual" in issue.suggestion

    def test_component_name_with_spaces(self):
        """Component names with spaces should be handled correctly."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.input.date-range",
                        "meta": {"name": "Date Range Picker"},
                        "children": [],
                    },
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "Consumer"},
                        "children": [],
                        "propConfig": {
                            "props.text": {
                                "binding": {
                                    "type": "property",
                                    "config": {
                                        "path": "/root/Date Range Picker.props.value"
                                    },
                                }
                            }
                        },
                    },
                ],
            },
        }
        issues = _lint_view(view)
        assert "BINDING_COMPONENT_NOT_FOUND" not in _codes(issues)

    def test_no_children_at_leaf(self):
        """Path pointing through a leaf component (no children) is flagged."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "Label"},
                        "children": [],
                    },
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "Consumer"},
                        "children": [],
                        "propConfig": {
                            "props.text": {
                                "binding": {
                                    "type": "property",
                                    "config": {"path": "/root/Label/Nested.props.text"},
                                }
                            }
                        },
                    },
                ],
            },
        }
        issues = _lint_view(view)
        assert "BINDING_COMPONENT_NOT_FOUND" in _codes(issues)
        issue = next(i for i in issues if i.code == "BINDING_COMPONENT_NOT_FOUND")
        assert "Nested" in issue.message
        assert "No children" in issue.suggestion


class TestExpressionPathResolution:
    """Tier 2: Verify {view.custom.X} and {view.params.X} in expressions."""

    def test_expr_view_custom_not_found(self):
        """{view.custom.missing} in an expression should be flagged."""
        view = {
            "custom": {"realProp": ""},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "expr",
                            "config": {
                                "expression": "if({view.custom.missing}, 'yes', 'no')"
                            },
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "EXPR_VIEW_PROP_NOT_FOUND" in _codes(issues)
        issue = next(i for i in issues if i.code == "EXPR_VIEW_PROP_NOT_FOUND")
        assert "missing" in issue.message

    def test_expr_view_params_not_found(self):
        """{view.params.missing} in an expression should be flagged."""
        view = {
            "custom": {},
            "params": {"existing": ""},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "expr",
                            "config": {"expression": "{view.params.missing}"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "EXPR_VIEW_PROP_NOT_FOUND" in _codes(issues)

    def test_expr_view_custom_found(self):
        """{view.custom.X} where X exists should not be flagged."""
        view = {
            "custom": {"myProp": "hello"},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "expr",
                            "config": {"expression": "{view.custom.myProp}"},
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "EXPR_VIEW_PROP_NOT_FOUND" not in _codes(issues)

    def test_expr_transform_view_ref_checked(self):
        """{view.custom.missing} in an expression transform should be flagged."""
        view = {
            "custom": {"realProp": ""},
            "root": {
                "type": "ia.display.label",
                "meta": {"name": "Label"},
                "children": [],
                "propConfig": {
                    "props.text": {
                        "binding": {
                            "type": "tag",
                            "config": {"tagPath": "[default]MyTag"},
                            "transforms": [
                                {
                                    "type": "expression",
                                    "expression": "if({view.custom.missing}, {value}, '')",
                                }
                            ],
                        }
                    }
                },
            },
        }
        issues = _lint_view(view)
        assert "EXPR_VIEW_PROP_NOT_FOUND" in _codes(issues)


class TestNonBindablePropertyDetection:
    """Tests for BINDING_NON_BINDABLE_PROPERTY rule.

    propConfig keys must start with props., position., custom., meta., or params.
    Structural keys like children, type have no binding scope and cause
    IllegalArgumentException in Ignition Designer.
    """

    def test_children_binding_flagged(self):
        """children is structural on containers — binding to it is always invalid."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.container.flex",
                        "meta": {"name": "SummaryBar"},
                        "children": [],
                        "propConfig": {
                            "children": {
                                "binding": {
                                    "type": "expr",
                                    "config": {"expression": "''"},
                                }
                            }
                        },
                    }
                ],
            },
        }
        issues = _lint_view(view)
        codes = _codes(issues)
        assert "BINDING_NON_BINDABLE_PROPERTY" in codes
        matching = [i for i in issues if i.code == "BINDING_NON_BINDABLE_PROPERTY"]
        assert len(matching) == 1
        assert "children" in matching[0].message
        assert matching[0].severity.value == "error"

    def test_type_binding_flagged(self):
        """type is structural — binding to it is invalid."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "Lbl"},
                        "propConfig": {
                            "type": {
                                "binding": {
                                    "type": "expr",
                                    "config": {"expression": "'ia.display.label'"},
                                }
                            }
                        },
                    }
                ],
            },
        }
        issues = _lint_view(view)
        assert "BINDING_NON_BINDABLE_PROPERTY" in _codes(issues)

    def test_valid_scopes_not_flagged(self):
        """props.*, position.*, custom.*, meta.*, params.* are all valid scopes."""
        view = {
            "custom": {"myFlag": False},
            "params": {"myParam": ""},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.display.label",
                        "meta": {"name": "Lbl"},
                        "propConfig": {
                            "props.text": {
                                "binding": {
                                    "type": "property",
                                    "config": {"path": "view.params.myParam"},
                                }
                            },
                            "position.basis": {
                                "binding": {
                                    "type": "expr",
                                    "config": {"expression": "'100px'"},
                                }
                            },
                            "meta.visible": {
                                "binding": {
                                    "type": "property",
                                    "config": {"path": "view.custom.myFlag"},
                                }
                            },
                        },
                    }
                ],
            },
        }
        issues = _lint_view(view)
        assert "BINDING_NON_BINDABLE_PROPERTY" not in _codes(issues)

    def test_onchange_on_structural_property_flagged(self):
        """Even onChange (not just binding) on a structural key is invalid."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.container.flex",
                        "meta": {"name": "Container"},
                        "children": [],
                        "propConfig": {"children": {"onChange": {"script": "\tpass"}}},
                    }
                ],
            },
        }
        issues = _lint_view(view)
        assert "BINDING_NON_BINDABLE_PROPERTY" in _codes(issues)

    def test_view_level_structural_propconfig_flagged(self):
        """Structural keys in view-level propConfig should also be flagged."""
        view = {
            "custom": {},
            "propConfig": {
                "children": {
                    "binding": {
                        "type": "expr",
                        "config": {"expression": "''"},
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
        codes = _codes(issues)
        assert "BINDING_NON_BINDABLE_PROPERTY" in codes

    def test_multiple_structural_keys_all_flagged(self):
        """Multiple invalid propConfig keys on the same component each get flagged."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [
                    {
                        "type": "ia.container.flex",
                        "meta": {"name": "Bad"},
                        "children": [],
                        "propConfig": {
                            "children": {
                                "binding": {
                                    "type": "expr",
                                    "config": {"expression": "''"},
                                }
                            },
                            "type": {
                                "binding": {
                                    "type": "expr",
                                    "config": {"expression": "''"},
                                }
                            },
                            "props.text": {
                                "binding": {
                                    "type": "expr",
                                    "config": {"expression": "'hello'"},
                                }
                            },
                        },
                    }
                ],
            },
        }
        issues = _lint_view(view)
        matching = [i for i in issues if i.code == "BINDING_NON_BINDABLE_PROPERTY"]
        flagged_keys = {i.message.split("'")[1] for i in matching}
        assert flagged_keys == {"children", "type"}


class TestParamDirectionValidation:
    """Tests for MISSING_PARAM_DIRECTION rule."""

    _BASE_ROOT = {
        "type": "ia.container.flex",
        "meta": {"name": "Root"},
        "children": [],
    }

    def test_param_no_propconfig_warns(self):
        """Params defined with no propConfig at all — the exact bug scenario."""
        view = {
            "custom": {},
            "params": {"itemId": 0, "mode": "view"},
            "root": self._BASE_ROOT,
        }
        issues = _lint_view(view)
        param_issues = [i for i in issues if i.code == "MISSING_PARAM_DIRECTION"]
        assert len(param_issues) == 2
        names = {i.component_path for i in param_issues}
        assert names == {"params.itemId", "params.mode"}
        assert all(i.severity.value == "warning" for i in param_issues)

    def test_param_propconfig_no_direction_warns(self):
        """propConfig entry exists for the param but lacks paramDirection."""
        view = {
            "custom": {},
            "params": {"cameraID": "abc"},
            "propConfig": {
                "params.cameraID": {
                    "persistent": True,
                }
            },
            "root": self._BASE_ROOT,
        }
        issues = _lint_view(view)
        assert "MISSING_PARAM_DIRECTION" in _codes(issues)
        matching = [i for i in issues if i.code == "MISSING_PARAM_DIRECTION"]
        assert len(matching) == 1
        assert matching[0].component_path == "propConfig.params.cameraID"

    def test_param_proper_propconfig_clean(self):
        """Complete propConfig with paramDirection — no warning."""
        view = {
            "custom": {},
            "params": {"cameraID": "abc"},
            "propConfig": {
                "params.cameraID": {
                    "paramDirection": "input",
                    "persistent": True,
                }
            },
            "root": self._BASE_ROOT,
        }
        issues = _lint_view(view)
        assert "MISSING_PARAM_DIRECTION" not in _codes(issues)

    def test_empty_params_no_warning(self):
        """Empty params dict should not trigger any warnings."""
        view = {
            "custom": {},
            "params": {},
            "root": self._BASE_ROOT,
        }
        issues = _lint_view(view)
        assert "MISSING_PARAM_DIRECTION" not in _codes(issues)

    def test_multiple_params_partial_propconfig(self):
        """Two params, one configured and one not — exactly one warning."""
        view = {
            "custom": {},
            "params": {"itemId": 0, "mode": "view"},
            "propConfig": {
                "params.itemId": {
                    "paramDirection": "input",
                    "persistent": True,
                }
            },
            "root": self._BASE_ROOT,
        }
        issues = _lint_view(view)
        matching = [i for i in issues if i.code == "MISSING_PARAM_DIRECTION"]
        assert len(matching) == 1
        assert matching[0].component_path == "params.mode"


class TestEventWrongCategory:
    """Tests for EVENT_WRONG_CATEGORY rule (TEC-2383)."""

    _BASE_VIEW = {
        "custom": {},
        "root": {
            "type": "ia.container.flex",
            "meta": {"name": "Root"},
            "children": [],
        },
    }

    @staticmethod
    def _make_view_with_event(category, event_name):
        """Build a minimal view.json with a single event handler."""
        return {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [],
                "events": {
                    category: {
                        event_name: {
                            "type": "script",
                            "config": {"script": "\tpass"},
                        }
                    }
                },
            },
        }

    def test_correct_system_event(self):
        """onStartup under events.system should not flag."""
        view = self._make_view_with_event("system", "onStartup")
        issues = _lint_view(view)
        assert "EVENT_WRONG_CATEGORY" not in _codes(issues)

    def test_correct_mouse_event(self):
        """onClick under events.mouse should not flag."""
        view = self._make_view_with_event("mouse", "onClick")
        issues = _lint_view(view)
        assert "EVENT_WRONG_CATEGORY" not in _codes(issues)

    def test_correct_component_event(self):
        """onActionPerformed under events.component should not flag."""
        view = self._make_view_with_event("component", "onActionPerformed")
        issues = _lint_view(view)
        assert "EVENT_WRONG_CATEGORY" not in _codes(issues)

    def test_system_event_under_component(self):
        """onStartup under events.component should flag."""
        view = self._make_view_with_event("component", "onStartup")
        issues = _lint_view(view)
        matching = [i for i in issues if i.code == "EVENT_WRONG_CATEGORY"]
        assert len(matching) == 1
        assert "system event" in matching[0].message
        assert matching[0].suggestion == "Move to events.system.onStartup"

    def test_mouse_event_under_system(self):
        """onClick under events.system should flag."""
        view = self._make_view_with_event("system", "onClick")
        issues = _lint_view(view)
        matching = [i for i in issues if i.code == "EVENT_WRONG_CATEGORY"]
        assert len(matching) == 1
        assert "mouse event" in matching[0].message
        assert matching[0].suggestion == "Move to events.mouse.onClick"

    def test_keyboard_event_under_mouse(self):
        """onKeyDown under events.mouse should flag."""
        view = self._make_view_with_event("mouse", "onKeyDown")
        issues = _lint_view(view)
        matching = [i for i in issues if i.code == "EVENT_WRONG_CATEGORY"]
        assert len(matching) == 1
        assert matching[0].suggestion == "Move to events.keyboard.onKeyDown"

    def test_focus_event_under_component(self):
        """onBlur under events.component should flag."""
        view = self._make_view_with_event("component", "onBlur")
        issues = _lint_view(view)
        matching = [i for i in issues if i.code == "EVENT_WRONG_CATEGORY"]
        assert len(matching) == 1
        assert matching[0].suggestion == "Move to events.focus.onBlur"

    def test_pointer_event_under_mouse(self):
        """onPointerDown under events.mouse should flag."""
        view = self._make_view_with_event("mouse", "onPointerDown")
        issues = _lint_view(view)
        matching = [i for i in issues if i.code == "EVENT_WRONG_CATEGORY"]
        assert len(matching) == 1
        assert matching[0].suggestion == "Move to events.pointer.onPointerDown"

    def test_unknown_event_not_flagged(self):
        """Custom/unknown events should not trigger this rule."""
        view = self._make_view_with_event("component", "onCustomThing")
        issues = _lint_view(view)
        assert "EVENT_WRONG_CATEGORY" not in _codes(issues)

    def test_multiple_wrong_events(self):
        """Multiple misplaced events should each produce a separate issue."""
        view = {
            "custom": {},
            "root": {
                "type": "ia.container.flex",
                "meta": {"name": "Root"},
                "children": [],
                "events": {
                    "component": {
                        "onStartup": {
                            "type": "script",
                            "config": {"script": "\tpass"},
                        },
                        "onShutdown": {
                            "type": "script",
                            "config": {"script": "\tpass"},
                        },
                    }
                },
            },
        }
        issues = _lint_view(view)
        matching = [i for i in issues if i.code == "EVENT_WRONG_CATEGORY"]
        assert len(matching) == 2
        event_names = {m.message.split("'")[1] for m in matching}
        assert event_names == {"onStartup", "onShutdown"}

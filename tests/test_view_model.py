"""Tests for the flattened ViewModel."""
import pytest

from ignition_lint.perspective.view_model import build_view_model, ViewModel


def test_extracts_custom_properties():
    view_data = {
        "custom": {"myProp": "hello", "count": 0},
        "params": {"id": 1},
        "root": {
            "type": "ia.container.flex",
            "children": [],
        },
    }
    model = build_view_model(view_data, "test/view.json")
    assert model.custom_property_names == {"myProp", "count"}
    assert model.param_property_names == {"id"}


def test_extracts_param_properties():
    view_data = {
        "custom": {},
        "params": {"pageId": "", "mode": "view"},
        "root": {"type": "ia.container.flex", "children": []},
    }
    model = build_view_model(view_data, "test/view.json")
    assert model.param_property_names == {"pageId", "mode"}
    props_by_name = {p.name: p for p in model.properties}
    assert props_by_name["mode"].default_value == "view"


def test_extracts_onchange_scripts():
    view_data = {
        "custom": {},
        "root": {
            "type": "ia.container.flex",
            "children": [],
            "propConfig": {
                "custom.myProp": {
                    "onChange": {"script": "\tprint('changed')"}
                }
            },
        },
    }
    model = build_view_model(view_data, "test/view.json")
    assert len(model.scripts) == 1
    assert model.scripts[0].script_type == "onChange"
    assert "print" in model.scripts[0].content


def test_extracts_event_scripts():
    view_data = {
        "custom": {},
        "root": {
            "type": "ia.input.button",
            "children": [],
            "events": {
                "dom": {
                    "onClick": [
                        {"type": "script", "config": {"script": "\tsystem.perspective.navigate('/home')"}}
                    ]
                }
            },
        },
    }
    model = build_view_model(view_data, "test/view.json")
    assert len(model.scripts) == 1
    assert model.scripts[0].script_type == "event"


def test_extracts_expressions_from_bindings():
    view_data = {
        "custom": {},
        "root": {
            "type": "ia.display.label",
            "children": [],
            "propConfig": {
                "props.text": {
                    "binding": {
                        "type": "expr",
                        "config": {"expression": "dateFormat(now(5000), 'HH:mm')"},
                    }
                }
            },
        },
    }
    model = build_view_model(view_data, "test/view.json")
    assert len(model.expressions) == 1
    assert "dateFormat" in model.expressions[0].content
    assert model.all_expression_text == ["dateFormat(now(5000), 'HH:mm')"]


def test_extracts_transform_scripts():
    view_data = {
        "custom": {},
        "root": {
            "type": "ia.display.label",
            "children": [],
            "propConfig": {
                "props.text": {
                    "binding": {
                        "type": "tag",
                        "config": {"tagPath": "[default]Tag"},
                        "transforms": [
                            {"type": "script", "code": "\treturn value * 2"}
                        ],
                    }
                }
            },
        },
    }
    model = build_view_model(view_data, "test/view.json")
    script_nodes = [s for s in model.scripts if s.script_type == "transform"]
    assert len(script_nodes) == 1
    assert "return value * 2" in script_nodes[0].content


def test_extracts_view_level_propconfig():
    view_data = {
        "custom": {"x": 1},
        "propConfig": {
            "custom.x": {
                "binding": {
                    "type": "expr",
                    "config": {"expression": "toInt({view.params.id})"},
                }
            }
        },
        "root": {"type": "ia.container.flex", "children": []},
    }
    model = build_view_model(view_data, "test/view.json")
    assert len(model.expressions) == 1
    assert "toInt" in model.expressions[0].content
    assert len(model.bindings) == 1
    assert model.bindings[0].binding_type == "expr"


def test_convenience_properties():
    view_data = {
        "custom": {},
        "root": {
            "type": "ia.display.label",
            "children": [],
            "propConfig": {
                "props.text": {
                    "binding": {
                        "type": "expr",
                        "config": {"expression": "now(5000)"},
                        "transforms": [
                            {"type": "script", "code": "\treturn str(value)"}
                        ],
                    }
                }
            },
        },
    }
    model = build_view_model(view_data, "test/view.json")
    assert len(model.all_expression_text) == 1
    assert len(model.all_script_text) == 1

"""Flattened view model for structured analysis of Perspective views."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class PropertyDef:
    """A custom or param property defined on a view."""

    name: str
    kind: str  # "custom" or "param"
    default_value: Any = None


@dataclass
class BindingNode:
    """A binding extracted from a view's propConfig tree."""

    prop_path: str
    binding_type: str  # "property", "expr", "tag", "expr-struct", "query", "tag-history"
    expression: Optional[str] = None
    property_path: Optional[str] = None
    tag_path: Optional[str] = None
    transforms: List[Dict[str, Any]] = field(default_factory=list)
    component_path: str = ""


@dataclass
class ScriptNode:
    """A script extracted from a view (event handler, onChange, or transform)."""

    content: str
    location: str  # descriptive path e.g. "root.events.onClick[0]"
    script_type: str  # "event", "onChange", "transform"
    component_path: str = ""


@dataclass
class ExpressionNode:
    """An expression extracted from a binding or transform."""

    content: str
    location: str  # descriptive path
    component_path: str = ""


@dataclass
class ViewModel:
    """Flattened representation of an Ignition Perspective view."""

    file_path: str
    properties: List[PropertyDef] = field(default_factory=list)
    bindings: List[BindingNode] = field(default_factory=list)
    scripts: List[ScriptNode] = field(default_factory=list)
    expressions: List[ExpressionNode] = field(default_factory=list)
    components: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def custom_property_names(self) -> Set[str]:
        return {p.name for p in self.properties if p.kind == "custom"}

    @property
    def param_property_names(self) -> Set[str]:
        return {p.name for p in self.properties if p.kind == "param"}

    @property
    def all_expression_text(self) -> List[str]:
        return [e.content for e in self.expressions]

    @property
    def all_script_text(self) -> List[str]:
        return [s.content for s in self.scripts]


def _extract_from_propconfig(
    prop_config: Dict[str, Any],
    component_path: str,
    bindings: List[BindingNode],
    scripts: List[ScriptNode],
    expressions: List[ExpressionNode],
) -> None:
    """Extract bindings, scripts, and expressions from a propConfig dict."""
    for prop_name, config in prop_config.items():
        if not isinstance(config, dict):
            continue

        # onChange scripts
        on_change = config.get("onChange")
        if isinstance(on_change, dict):
            script_code = on_change.get("script", "")
            if script_code:
                scripts.append(ScriptNode(
                    content=script_code,
                    location=f"{component_path}.propConfig.{prop_name}.onChange",
                    script_type="onChange",
                    component_path=component_path,
                ))

        # Bindings
        binding = config.get("binding")
        if not isinstance(binding, dict):
            continue

        binding_type = binding.get("type", "")
        binding_config = binding.get("config", {})

        node = BindingNode(
            prop_path=prop_name,
            binding_type=binding_type,
            transforms=binding.get("transforms", []),
            component_path=component_path,
        )

        if binding_type == "expr" and isinstance(binding_config, dict):
            expr = binding_config.get("expression", "")
            node.expression = expr
            if expr:
                expressions.append(ExpressionNode(
                    content=expr,
                    location=f"{component_path}.propConfig.{prop_name}.binding.expr",
                    component_path=component_path,
                ))

        if binding_type == "expr-struct" and isinstance(binding_config, dict):
            struct = binding_config.get("struct", {})
            if isinstance(struct, dict):
                for member, expr in struct.items():
                    if isinstance(expr, str) and expr.strip():
                        expressions.append(ExpressionNode(
                            content=expr,
                            location=f"{component_path}.propConfig.{prop_name}.binding.struct.{member}",
                            component_path=component_path,
                        ))

        if binding_type == "property" and isinstance(binding_config, dict):
            node.property_path = binding_config.get("path")

        if binding_type == "tag" and isinstance(binding_config, dict):
            node.tag_path = binding_config.get("tagPath")

        bindings.append(node)

        # Transform scripts and expressions
        for i, transform in enumerate(binding.get("transforms", [])):
            if not isinstance(transform, dict):
                continue
            t_type = transform.get("type")
            if t_type == "script":
                code = transform.get("code", "")
                if code:
                    scripts.append(ScriptNode(
                        content=code,
                        location=f"{component_path}.propConfig.{prop_name}.transforms[{i}]",
                        script_type="transform",
                        component_path=component_path,
                    ))
            if t_type == "expression":
                expr = transform.get("expression", "")
                if expr:
                    expressions.append(ExpressionNode(
                        content=expr,
                        location=f"{component_path}.propConfig.{prop_name}.transforms[{i}]",
                        component_path=component_path,
                    ))


def _extract_from_tree(
    obj: Any,
    path: str,
    components: List[Dict[str, Any]],
    bindings: List[BindingNode],
    scripts: List[ScriptNode],
    expressions: List[ExpressionNode],
) -> None:
    """Walk the component tree extracting events and propConfig."""
    if not isinstance(obj, dict):
        return

    if "type" in obj and isinstance(obj.get("type"), str) and obj["type"].startswith("ia."):
        components.append(obj)

    # propConfig
    prop_config = obj.get("propConfig", {})
    if isinstance(prop_config, dict):
        _extract_from_propconfig(prop_config, path, bindings, scripts, expressions)

    # Event scripts
    events = obj.get("events", {})
    if isinstance(events, dict):
        for category, handlers in events.items():
            if not isinstance(handlers, dict):
                continue
            for event_name, handler_config in handlers.items():
                handlers_list = handler_config if isinstance(handler_config, list) else [handler_config]
                for j, handler in enumerate(handlers_list):
                    if isinstance(handler, dict) and handler.get("type") == "script":
                        code = handler.get("config", {}).get("script", "")
                        if code:
                            scripts.append(ScriptNode(
                                content=code,
                                location=f"{path}.events.{category}.{event_name}[{j}]",
                                script_type="event",
                                component_path=path,
                            ))

    # Recurse into children
    children = obj.get("children", [])
    if isinstance(children, list):
        for i, child in enumerate(children):
            _extract_from_tree(child, f"{path}.children[{i}]", components, bindings, scripts, expressions)

    # Recurse into root
    if "root" in obj:
        _extract_from_tree(obj["root"], f"{path}.root", components, bindings, scripts, expressions)


def build_view_model(view_data: Dict[str, Any], file_path: str) -> ViewModel:
    """Build a flattened ViewModel from raw view.json data."""
    model = ViewModel(file_path=file_path)

    # Extract custom properties
    custom = view_data.get("custom", {})
    if isinstance(custom, dict):
        for name, value in custom.items():
            model.properties.append(PropertyDef(name=name, kind="custom", default_value=value))

    # Extract param properties
    params = view_data.get("params", {})
    if isinstance(params, dict):
        for name, value in params.items():
            model.properties.append(PropertyDef(name=name, kind="param", default_value=value))

    # Walk view-level propConfig
    view_prop_config = view_data.get("propConfig", {})
    if isinstance(view_prop_config, dict):
        _extract_from_propconfig(
            view_prop_config, "view", model.bindings, model.scripts, model.expressions
        )

    # Walk the component tree (start from root, not view_data, to avoid
    # double-processing the view-level propConfig)
    root = view_data.get("root")
    if isinstance(root, dict):
        _extract_from_tree(
            root, "root", model.components, model.bindings, model.scripts, model.expressions
        )

    return model

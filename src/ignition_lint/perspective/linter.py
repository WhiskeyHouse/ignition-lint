#!/usr/bin/env python3
"""
Ignition Perspective Component Linter

A robust linting tool for Ignition Perspective view.json files that validates:
- Component structure against empirical schema
- Property usage patterns
- Best practices compliance
- Performance considerations

Usage:
    uv run python ignition-perspective-linter.py --target /path/to/ignition/project
    uv run python ignition-perspective-linter.py --target /path/to/ignition/project --verbose
    uv run python ignition-perspective-linter.py --target /path/to/ignition/project --component-type ia.display.label
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    validate = None  # type: ignore[var-annotated]
    JSONSCHEMA_AVAILABLE = False

    class ValidationError(Exception):
        """Fallback error when jsonschema is unavailable."""

        pass

from ..reporting import LintIssue, LintSeverity
from ..schemas import schema_path_for as _schema_path_for
from ..validators.expression import ExpressionValidator
from ..validators.jython import JythonValidator

class IgnitionPerspectiveLinter:
    def __init__(self, schema_path: str = None):
        """Initialize the linter with the component schema."""
        if schema_path is None:
            schema_path = _schema_path_for("robust")
        else:
            schema_path = Path(schema_path)

        self.schema_path = schema_path
        self.jsonschema_available = JSONSCHEMA_AVAILABLE and validate is not None
        self.schema = self._load_schema(schema_path)
        self.issues: List[LintIssue] = []
        self.component_stats = {
            'total_files': 0,
            'total_components': 0,
            'valid_components': 0,
            'invalid_components': 0,
            'component_types': set()
        }
        self._missing_schema_files: Set[str] = set()
        self.jython_validator = JythonValidator()
        self.expression_validator = ExpressionValidator()
        
        # Known best practices patterns
        self.best_practices = {
            'preferred_containers': ['ia.container.flex'],
            'deprecated_patterns': [],
            'required_meta_properties': ['name'],
            'performance_concerns': {
                'ia.display.flex-repeater': 'Consider performance impact with large datasets',
                'ia.display.table': 'Large tables may impact rendering performance',
                'ia.chart.xy': 'Complex charts with many data points may be slow'
            }
        }
    
    def _load_schema(self, schema_path: str) -> dict:
        """Load the JSON schema for validation."""
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Schema file not found: {schema_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in schema file: {e}")
            sys.exit(1)
    
    def find_view_files(self, target_path: str) -> List[str]:
        """Find all view.json files in the target directory."""
        view_files = []
        target = Path(target_path)
        
        if not target.exists():
            print(f"ERROR: Target path does not exist: {target_path}")
            return []
        
        # Look for perspective views structure
        perspective_path = target / "com.inductiveautomation.perspective" / "views"
        if perspective_path.exists():
            search_path = perspective_path
        else:
            search_path = target
            
        for root, dirs, files in os.walk(search_path):
            for file in files:
                if file == "view.json":
                    view_files.append(os.path.join(root, file))
        
        return view_files
    
    def extract_components_with_context(self, view_data: dict, file_path: str) -> List[Tuple[dict, str, str]]:
        """Extract all ia.* components with their context path."""
        components = []
        
        def extract_recursive(obj, path="root"):
            if isinstance(obj, dict):
                if 'type' in obj and isinstance(obj['type'], str) and obj['type'].startswith('ia.'):
                    components.append((obj, file_path, path))
                
                if 'children' in obj and isinstance(obj['children'], list):
                    for i, child in enumerate(obj['children']):
                        extract_recursive(child, f"{path}.children[{i}]")
                
                if 'root' in obj:
                    extract_recursive(obj['root'], f"{path}.root")
        
        extract_recursive(view_data)
        return components
    
    def validate_component_schema(self, component: dict, file_path: str, component_path: str) -> bool:
        """Validate a component against the schema."""
        if not self.jsonschema_available or validate is None:
            if file_path not in self._missing_schema_files:
                self._missing_schema_files.add(file_path)
                self.issues.append(LintIssue(
                    severity=LintSeverity.WARNING,
                    code="SCHEMA_VALIDATION_SKIPPED",
                    message="Schema validation skipped because the 'jsonschema' package is not available.",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component.get('type', 'unknown'),
                    suggestion="Install the 'jsonschema' package to enable schema validation.",
                ))
            return True

        try:
            validate(instance=component, schema=self.schema)
            return True
        except ValidationError as e:
            self.issues.append(LintIssue(
                severity=LintSeverity.ERROR,
                code="SCHEMA_VALIDATION",
                message=f"Schema validation failed: {e.message}",
                file_path=file_path,
                component_path=component_path,
                component_type=component.get('type', 'unknown'),
                suggestion=f"Path: {'.'.join(map(str, e.absolute_path))}" if e.absolute_path else None
            ))
            return False
    
    def check_component_best_practices(self, component: dict, file_path: str, component_path: str):
        """Check component against best practices."""
        comp_type = component.get('type', '')
        
        # Check for required meta properties
        meta = component.get('meta', {})
        for required_prop in self.best_practices['required_meta_properties']:
            if required_prop not in meta:
                self.issues.append(LintIssue(
                    severity=LintSeverity.WARNING,
                    code="MISSING_META_PROPERTY",
                    message=f"Missing required meta property: '{required_prop}'",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=comp_type,
                    suggestion=f"Add 'meta.{required_prop}' property"
                ))
        
        # Check for empty or generic names
        name = meta.get('name', '')
        if not name:
            self.issues.append(LintIssue(
                severity=LintSeverity.WARNING,
                code="EMPTY_COMPONENT_NAME",
                message="Component has empty or missing name",
                file_path=file_path,
                component_path=component_path,
                component_type=comp_type,
                suggestion="Provide a descriptive name for debugging and maintenance"
            ))
        elif name in ['Component', 'View', 'Container', 'Label', 'Button']:
            self.issues.append(LintIssue(
                severity=LintSeverity.STYLE,
                code="GENERIC_COMPONENT_NAME",
                message=f"Generic component name '{name}' should be more descriptive",
                file_path=file_path,
                component_path=component_path,
                component_type=comp_type,
                suggestion="Use descriptive names like 'StatusLabel', 'SubmitButton', etc."
            ))
        
        # Check for performance concerns
        if comp_type in self.best_practices['performance_concerns']:
            self.issues.append(LintIssue(
                severity=LintSeverity.INFO,
                code="PERFORMANCE_CONSIDERATION",
                message=self.best_practices['performance_concerns'][comp_type],
                file_path=file_path,
                component_path=component_path,
                component_type=comp_type
            ))
        
        # Check for missing position properties in containers
        if comp_type.startswith('ia.container.') and 'children' in component:
            children = component.get('children', [])
            for i, child in enumerate(children):
                if 'position' not in child:
                    self.issues.append(LintIssue(
                        severity=LintSeverity.WARNING,
                        code="MISSING_CHILD_POSITION",
                        message=f"Child component at index {i} missing position properties",
                        file_path=file_path,
                        component_path=f"{component_path}.children[{i}]",
                        component_type=child.get('type', 'unknown'),
                        suggestion="Add position properties for proper layout"
                    ))
        
        # Check for inefficient flex container usage
        if comp_type == 'ia.container.flex':
            props = component.get('props', {})
            children = component.get('children', [])
            
            # Single child in flex container might be unnecessary
            if len(children) == 1:
                self.issues.append(LintIssue(
                    severity=LintSeverity.STYLE,
                    code="SINGLE_CHILD_FLEX",
                    message="Flex container with single child may be unnecessary",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=comp_type,
                    suggestion="Consider if flex container is needed for single child"
                ))
            
            # Check for missing direction property
            if 'direction' not in props and len(children) > 1:
                self.issues.append(LintIssue(
                    severity=LintSeverity.INFO,
                    code="MISSING_FLEX_DIRECTION",
                    message="Flex container missing explicit direction property",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=comp_type,
                    suggestion="Add 'props.direction' for explicit layout control"
                ))
        
        # Validate bindings
        self._validate_bindings(component, file_path, component_path)
        
        # Validate event handler Jython scripts
        self._validate_event_scripts(component, file_path, component_path)

        # Validate onChange scripts in propConfig
        self._validate_onchange_scripts(component, file_path, component_path)

        # Validate expression bindings and transforms
        self._validate_expressions(component, file_path, component_path)

        # Check for missing text in labels
        if comp_type == 'ia.display.label':
            props = component.get('props', {})
            prop_config = component.get('propConfig', {})
            
            # Check if text is provided either directly or via binding
            has_text = 'text' in props
            has_text_binding = 'props.text' in prop_config
            
            if not has_text and not has_text_binding:
                self.issues.append(LintIssue(
                    severity=LintSeverity.WARNING,
                    code="MISSING_LABEL_TEXT",
                    message="Label component missing text content or binding",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=comp_type,
                    suggestion="Add 'props.text' or 'propConfig.props.text.binding'"
                ))
        
        # Check for missing path in icons
        if comp_type == 'ia.display.icon':
            props = component.get('props', {})
            if 'path' not in props:
                self.issues.append(LintIssue(
                    severity=LintSeverity.ERROR,
                    code="MISSING_ICON_PATH",
                    message="Icon component missing required path property",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=comp_type,
                    suggestion="Add 'props.path' with icon reference"
                ))
    
    def check_component_accessibility(self, component: dict, file_path: str, component_path: str):
        """Check component for accessibility best practices."""
        comp_type = component.get('type', '')
        
        # Check for interactive components without proper labeling
        interactive_types = [
            'ia.input.button', 'ia.input.dropdown', 'ia.input.text-field',
            'ia.input.checkbox', 'ia.input.toggle-switch'
        ]
        
        if comp_type in interactive_types:
            props = component.get('props', {})
            meta = component.get('meta', {})
            
            # Check for descriptive text or aria labels
            has_text = 'text' in props
            has_placeholder = 'placeholder' in props
            has_name = 'name' in meta and meta['name'] not in ['Component', 'Button', 'Input']
            
            if not (has_text or has_placeholder or has_name):
                self.issues.append(LintIssue(
                    severity=LintSeverity.INFO,
                    code="ACCESSIBILITY_LABELING",
                    message="Interactive component may need better labeling for accessibility",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=comp_type,
                    suggestion="Add descriptive text, placeholder, or meaningful name"
                ))
    
    def _validate_bindings(self, component: dict, file_path: str, component_path: str):
        """Validate bindings based on empirical analysis patterns."""
        prop_config = component.get('propConfig', {})
        comp_type = component.get('type', 'unknown')
        
        # Validate each property binding
        for prop_name, config in prop_config.items():
            if 'binding' not in config:
                continue
                
            binding = config['binding']
            binding_type = binding.get('type')
            binding_config = binding.get('config', {})
            transforms = binding.get('transforms', [])
            
            # Validate binding type
            valid_binding_types = ['property', 'expr', 'tag', 'expr-struct', 'query', 'tag-history']
            if binding_type not in valid_binding_types:
                self.issues.append(LintIssue(
                    severity=LintSeverity.ERROR,
                    code="INVALID_BINDING_TYPE",
                    message=f"Invalid binding type '{binding_type}' for {prop_name}",
                    file_path=file_path,
                    component_path=f"{component_path}.propConfig.{prop_name}",
                    component_type=comp_type,
                    suggestion=f"Use one of: {', '.join(valid_binding_types)}"
                ))
            
            # Validate type-specific configurations
            if binding_type == 'tag':
                self._validate_tag_binding(binding_config, prop_name, file_path, component_path, comp_type)
            elif binding_type == 'expr':
                self._validate_expr_binding(binding_config, prop_name, file_path, component_path, comp_type)
            elif binding_type == 'property':
                self._validate_property_binding(binding_config, prop_name, file_path, component_path, comp_type)
            
            # Validate transforms
            for i, transform in enumerate(transforms):
                self._validate_transform(transform, prop_name, i, file_path, component_path, comp_type)
    
    def _validate_tag_binding(self, config: dict, prop_name: str, file_path: str, component_path: str, comp_type: str):
        """Validate tag binding configuration."""
        if 'tagPath' not in config:
            self.issues.append(LintIssue(
                severity=LintSeverity.ERROR,
                code="MISSING_TAG_PATH",
                message=f"Tag binding for {prop_name} missing required 'tagPath'",
                file_path=file_path,
                component_path=f"{component_path}.propConfig.{prop_name}",
                component_type=comp_type,
                suggestion="Add 'tagPath' property to tag binding config"
            ))
        
        # Check for fallback handling on critical properties
        if prop_name in ['props.text', 'props.value'] and 'fallbackDelay' not in config:
            self.issues.append(LintIssue(
                severity=LintSeverity.INFO,
                code="MISSING_TAG_FALLBACK",
                message=f"Tag binding for {prop_name} should include fallback handling",
                file_path=file_path,
                component_path=f"{component_path}.propConfig.{prop_name}",
                component_type=comp_type,
                suggestion="Consider adding 'fallbackDelay' for better error handling"
            ))
    
    def _validate_expr_binding(self, config: dict, prop_name: str, file_path: str, component_path: str, comp_type: str):
        """Validate expression binding configuration."""
        if 'expression' not in config:
            self.issues.append(LintIssue(
                severity=LintSeverity.ERROR,
                code="MISSING_EXPRESSION",
                message=f"Expression binding for {prop_name} missing required 'expression'",
                file_path=file_path,
                component_path=f"{component_path}.propConfig.{prop_name}",
                component_type=comp_type,
                suggestion="Add 'expression' property to expression binding config"
            ))
    
    def _validate_property_binding(self, config: dict, prop_name: str, file_path: str, component_path: str, comp_type: str):
        """Validate property binding configuration."""
        if 'path' not in config:
            self.issues.append(LintIssue(
                severity=LintSeverity.ERROR,
                code="MISSING_PROPERTY_PATH",
                message=f"Property binding for {prop_name} missing required 'path'",
                file_path=file_path,
                component_path=f"{component_path}.propConfig.{prop_name}",
                component_type=comp_type,
                suggestion="Add 'path' property to property binding config"
            ))
    
    def _validate_transform(self, transform: dict, prop_name: str, index: int, file_path: str, component_path: str, comp_type: str):
        """Validate transform configuration."""
        transform_type = transform.get('type')
        valid_transform_types = ['map', 'script', 'expression', 'format']
        
        if transform_type not in valid_transform_types:
            self.issues.append(LintIssue(
                severity=LintSeverity.ERROR,
                code="INVALID_TRANSFORM_TYPE",
                message=f"Invalid transform type '{transform_type}' for {prop_name}",
                file_path=file_path,
                component_path=f"{component_path}.propConfig.{prop_name}.transforms[{index}]",
                component_type=comp_type,
                suggestion=f"Use one of: {', '.join(valid_transform_types)}"
            ))
        
        # Validate type-specific requirements
        if transform_type == 'script':
            if 'code' not in transform:
                self.issues.append(LintIssue(
                    severity=LintSeverity.ERROR,
                    code="MISSING_SCRIPT_CODE",
                    message=f"Script transform for {prop_name} missing 'code' property",
                    file_path=file_path,
                    component_path=f"{component_path}.propConfig.{prop_name}.transforms[{index}]",
                    component_type=comp_type,
                    suggestion="Add 'code' property with Jython script"
                ))
            else:
                # Validate the Jython script content
                script_code = transform['code']
                context = f"transform[{index}]"
                self._validate_jython_script(script_code, prop_name, context, file_path, component_path, comp_type)
        
        if transform_type == 'expression' and 'expression' not in transform:
            self.issues.append(LintIssue(
                severity=LintSeverity.ERROR,
                code="MISSING_TRANSFORM_EXPRESSION",
                message=f"Expression transform for {prop_name} missing 'expression' property",
                file_path=file_path,
                component_path=f"{component_path}.propConfig.{prop_name}.transforms[{index}]",
                component_type=comp_type,
                suggestion="Add 'expression' property with transform expression"
            ))
        
        if transform_type == 'map':
            if 'mappings' not in transform:
                self.issues.append(LintIssue(
                    severity=LintSeverity.WARNING,
                    code="MISSING_MAP_MAPPINGS",
                    message=f"Map transform for {prop_name} missing 'mappings' array",
                    file_path=file_path,
                    component_path=f"{component_path}.propConfig.{prop_name}.transforms[{index}]",
                    component_type=comp_type,
                    suggestion="Add 'mappings' array with input/output pairs"
                ))
            
            # Check for fallback value on map transforms
            if 'fallback' not in transform:
                self.issues.append(LintIssue(
                    severity=LintSeverity.INFO,
                    code="MISSING_MAP_FALLBACK",
                    message=f"Map transform for {prop_name} should include fallback value",
                    file_path=file_path,
                    component_path=f"{component_path}.propConfig.{prop_name}.transforms[{index}]",
                    component_type=comp_type,
                    suggestion="Add 'fallback' property for unmapped values"
                ))
    
    def _validate_jython_script(self, script_content: str, prop_name: str, context: str, file_path: str, component_path: str, comp_type: str):
        """Validate inline Jython scripts using the shared validator."""
        if not script_content or not script_content.strip():
            return

        validator_issues = self.jython_validator.validate_script(script_content, context=context)
        for issue in validator_issues:
            issue.file_path = file_path
            issue.component_path = f"{component_path}.{prop_name}"
            issue.component_type = comp_type
            self.issues.append(issue)

    def _validate_event_scripts(self, component: dict, file_path: str, component_path: str):
        """Validate Jython scripts in event handlers."""
        events = component.get('events', {})
        comp_type = component.get('type', 'unknown')
        
        for event_category, handlers in events.items():
            if isinstance(handlers, dict):
                for event_name, handler_config in handlers.items():
                    # Handle both single handler and array of handlers
                    handlers_list = handler_config if isinstance(handler_config, list) else [handler_config]
                    
                    for j, handler in enumerate(handlers_list):
                        if isinstance(handler, dict) and handler.get('type') == 'script':
                            script_code = handler.get('config', {}).get('script', '')
                            if script_code:
                                context = f"event.{event_category}.{event_name}[{j}]"
                                prop_name = f"events.{event_category}.{event_name}"
                                self._validate_jython_script(script_code, prop_name, context, file_path, component_path, comp_type)
    
    def _validate_expressions(self, component: dict, file_path: str, component_path: str):
        """Validate expression bindings and expression transforms in a component."""
        prop_config = component.get('propConfig', {})
        comp_type = component.get('type', 'unknown')

        for prop_name, config in prop_config.items():
            if not isinstance(config, dict):
                continue

            binding = config.get('binding')
            if not isinstance(binding, dict):
                continue

            binding_type = binding.get('type')
            binding_config = binding.get('config', {})

            # expr bindings
            if binding_type == 'expr' and isinstance(binding_config, dict):
                expression = binding_config.get('expression', '')
                if expression:
                    self.issues.extend(self.expression_validator.validate_expression(
                        expression, f"expr({prop_name})",
                        file_path, f"{component_path}.propConfig.{prop_name}",
                        comp_type,
                    ))

            # expr-struct bindings - each member has its own expression
            if binding_type == 'expr-struct' and isinstance(binding_config, dict):
                struct = binding_config.get('struct', {})
                if isinstance(struct, dict):
                    for member_name, member_expr in struct.items():
                        if isinstance(member_expr, str) and member_expr.strip():
                            self.issues.extend(self.expression_validator.validate_expression(
                                member_expr, f"expr-struct({prop_name}.{member_name})",
                                file_path, f"{component_path}.propConfig.{prop_name}.{member_name}",
                                comp_type,
                            ))

            # Expression transforms
            transforms = binding.get('transforms', [])
            for i, transform in enumerate(transforms):
                if isinstance(transform, dict) and transform.get('type') == 'expression':
                    expr_text = transform.get('expression', '')
                    if expr_text:
                        self.issues.extend(self.expression_validator.validate_expression(
                            expr_text, f"transform[{i}]({prop_name})",
                            file_path, f"{component_path}.propConfig.{prop_name}.transforms[{i}]",
                            comp_type,
                        ))

    def _validate_propconfig_expressions(self, prop_config: dict, file_path: str, context_prefix: str):
        """Validate expression bindings in a propConfig dict (for view-level usage)."""
        for prop_name, config in prop_config.items():
            if not isinstance(config, dict):
                continue

            binding = config.get('binding')
            if not isinstance(binding, dict):
                continue

            binding_type = binding.get('type')
            binding_config = binding.get('config', {})

            if binding_type == 'expr' and isinstance(binding_config, dict):
                expression = binding_config.get('expression', '')
                if expression:
                    self.issues.extend(self.expression_validator.validate_expression(
                        expression, f"view.expr({prop_name})",
                        file_path, f"{context_prefix}.propConfig.{prop_name}",
                        "view",
                    ))

            if binding_type == 'expr-struct' and isinstance(binding_config, dict):
                struct = binding_config.get('struct', {})
                if isinstance(struct, dict):
                    for member_name, member_expr in struct.items():
                        if isinstance(member_expr, str) and member_expr.strip():
                            self.issues.extend(self.expression_validator.validate_expression(
                                member_expr, f"view.expr-struct({prop_name}.{member_name})",
                                file_path, f"{context_prefix}.propConfig.{prop_name}.{member_name}",
                                "view",
                            ))

            transforms = binding.get('transforms', [])
            for i, transform in enumerate(transforms):
                if isinstance(transform, dict) and transform.get('type') == 'expression':
                    expr_text = transform.get('expression', '')
                    if expr_text:
                        self.issues.extend(self.expression_validator.validate_expression(
                            expr_text, f"view.transform[{i}]({prop_name})",
                            file_path, f"{context_prefix}.propConfig.{prop_name}.transforms[{i}]",
                            "view",
                        ))

    def _validate_onchange_scripts(self, component: dict, file_path: str, component_path: str):
        """Validate onChange scripts within a component's propConfig."""
        prop_config = component.get('propConfig', {})
        comp_type = component.get('type', 'unknown')

        for prop_name, config in prop_config.items():
            on_change = config.get('onChange') if isinstance(config, dict) else None
            if not isinstance(on_change, dict):
                continue
            script_code = on_change.get('script', '')
            if script_code:
                context = f"onChange({prop_name})"
                self._validate_jython_script(
                    script_code, f"propConfig.{prop_name}.onChange",
                    context, file_path, component_path, comp_type,
                )

    def _validate_propconfig_scripts(self, prop_config: dict, file_path: str, context_prefix: str):
        """Validate onChange and transform scripts in a propConfig dict (view-level or component-level)."""
        for prop_name, config in prop_config.items():
            if not isinstance(config, dict):
                continue

            # onChange scripts
            on_change = config.get('onChange')
            if isinstance(on_change, dict):
                script_code = on_change.get('script', '')
                if script_code:
                    context = f"{context_prefix}.onChange({prop_name})"
                    self._validate_jython_script(
                        script_code, f"propConfig.{prop_name}.onChange",
                        context, file_path, context_prefix, "view",
                    )

            # Transform scripts on bindings
            binding = config.get('binding')
            if isinstance(binding, dict):
                transforms = binding.get('transforms', [])
                for i, transform in enumerate(transforms):
                    if isinstance(transform, dict) and transform.get('type') == 'script':
                        script_code = transform.get('code', '')
                        if script_code:
                            context = f"{context_prefix}.binding.transform[{i}]"
                            self._validate_jython_script(
                                script_code, f"propConfig.{prop_name}.binding.transforms[{i}]",
                                context, file_path, context_prefix, "view",
                            )

    @staticmethod
    def _collect_all_strings(obj: Any) -> List[str]:
        """Recursively collect all string values from a JSON structure."""
        strings: List[str] = []
        if isinstance(obj, str):
            strings.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                strings.extend(IgnitionPerspectiveLinter._collect_all_strings(v))
        elif isinstance(obj, list):
            for item in obj:
                strings.extend(IgnitionPerspectiveLinter._collect_all_strings(item))
        return strings

    @staticmethod
    def _collect_propconfig_keys(obj: Any, prefix: str = "") -> Set[str]:
        """Recursively collect all propConfig key paths from a JSON structure."""
        keys: Set[str] = set()
        if isinstance(obj, dict):
            prop_config = obj.get('propConfig', {})
            if isinstance(prop_config, dict):
                for k in prop_config:
                    keys.add(k)
            for v in obj.values():
                keys.update(IgnitionPerspectiveLinter._collect_propconfig_keys(v))
        elif isinstance(obj, list):
            for item in obj:
                keys.update(IgnitionPerspectiveLinter._collect_propconfig_keys(item))
        return keys

    def _check_unused_properties(self, view_data: dict, file_path: str):
        """Check for custom and param properties that appear unreferenced within the view."""
        custom_props = view_data.get('custom', {})
        params_props = view_data.get('params', {})

        if not custom_props and not params_props:
            return

        # Collect all strings and propConfig keys from the entire view
        all_strings = self._collect_all_strings(view_data)
        all_text = "\n".join(all_strings)
        propconfig_keys = self._collect_propconfig_keys(view_data)

        # Check custom properties
        if isinstance(custom_props, dict):
            for prop_name in custom_props:
                # Search for references in expressions, scripts, and propConfig keys
                expr_ref = f"view.custom.{prop_name}"
                script_ref = f"self.view.custom.{prop_name}"
                binding_target = f"custom.{prop_name}"

                found = (
                    expr_ref in all_text
                    or script_ref in all_text
                    or binding_target in propconfig_keys
                )
                if not found:
                    self.issues.append(LintIssue(
                        severity=LintSeverity.WARNING,
                        code="UNUSED_CUSTOM_PROPERTY",
                        message=f"Custom property '{prop_name}' appears unreferenced in this view",
                        file_path=file_path,
                        component_path=f"custom.{prop_name}",
                        component_type="view",
                        suggestion="Remove if unused, or verify it's referenced by an embedding view",
                    ))

        # Check param properties
        if isinstance(params_props, dict):
            for prop_name in params_props:
                expr_ref = f"view.params.{prop_name}"
                script_ref = f"self.view.params.{prop_name}"
                binding_target = f"params.{prop_name}"

                found = (
                    expr_ref in all_text
                    or script_ref in all_text
                    or binding_target in propconfig_keys
                )
                if not found:
                    self.issues.append(LintIssue(
                        severity=LintSeverity.INFO,
                        code="UNUSED_PARAM_PROPERTY",
                        message=f"Param property '{prop_name}' appears unreferenced in this view",
                        file_path=file_path,
                        component_path=f"params.{prop_name}",
                        component_type="view",
                        suggestion="Params may be set by embedding views; verify before removing",
                    ))

    def lint_file(self, file_path: str, target_component_type: Optional[str] = None) -> bool:
        """Lint a single view.json file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                view_data = json.load(f)
        except json.JSONDecodeError as e:
            self.issues.append(LintIssue(
                severity=LintSeverity.ERROR,
                code="INVALID_JSON",
                message=f"Invalid JSON format: {e}",
                file_path=file_path,
                component_path="file",
                component_type="view",
                suggestion=f"Line {e.lineno}: {e.msg}"
            ))
            return False
        except Exception as e:
            self.issues.append(LintIssue(
                severity=LintSeverity.ERROR,
                code="FILE_READ_ERROR",
                message=f"Could not read file: {e}",
                file_path=file_path,
                component_path="file",
                component_type="view"
            ))
            return False
        
        # Validate view-level propConfig (onChange scripts, transform scripts, expressions)
        view_prop_config = view_data.get('propConfig', {})
        if isinstance(view_prop_config, dict):
            self._validate_propconfig_scripts(view_prop_config, file_path, "view")
            self._validate_propconfig_expressions(view_prop_config, file_path, "view")

        # Extract components
        components = self.extract_components_with_context(view_data, file_path)
        
        if not components:
            self.issues.append(LintIssue(
                severity=LintSeverity.INFO,
                code="NO_COMPONENTS",
                message="No ia.* components found in view",
                file_path=file_path,
                component_path="root",
                component_type="view"
            ))
            return True
        
        # Filter by component type if specified
        if target_component_type:
            components = [(comp, fp, path) for comp, fp, path in components 
                         if comp.get('type', '').startswith(target_component_type)]
        
        file_valid = True
        for component, _, component_path in components:
            comp_type = component.get('type', 'unknown')
            self.component_stats['component_types'].add(comp_type)
            self.component_stats['total_components'] += 1
            
            # Schema validation
            is_valid = self.validate_component_schema(component, file_path, component_path)
            if is_valid:
                self.component_stats['valid_components'] += 1
            else:
                self.component_stats['invalid_components'] += 1
                file_valid = False
            
            # Best practices checks
            self.check_component_best_practices(component, file_path, component_path)
            
            # Accessibility checks
            self.check_component_accessibility(component, file_path, component_path)

        # Check for unused custom/param properties (per-view)
        self._check_unused_properties(view_data, file_path)

        return file_valid
    
    def lint_project(self, target_path: str, target_component_type: Optional[str] = None) -> Dict[str, Any]:
        """Lint an entire Ignition project."""
        print(f"🔍 Ignition Perspective Linter")
        print(f"Target: {target_path}")
        if target_component_type:
            print(f"Component Filter: {target_component_type}")
        print("=" * 60)
        
        if not self.jsonschema_available:
            print("⚠️  jsonschema dependency not available; skipping schema validation checks.")
        
        view_files = self.find_view_files(target_path)
        
        if not view_files:
            print("❌ No view.json files found in target directory")
            return {'success': False, 'message': 'No view files found'}
        
        print(f"📁 Found {len(view_files)} view files")
        
        self.component_stats['total_files'] = len(view_files)
        valid_files = 0
        
        for i, file_path in enumerate(view_files, 1):
            if i % 50 == 0:
                print(f"   Processing file {i}/{len(view_files)}...")
            
            file_valid = self.lint_file(file_path, target_component_type)
            if file_valid:
                valid_files += 1
        
        return {
            'success': True,
            'total_files': len(view_files),
            'valid_files': valid_files,
            'total_issues': len(self.issues),
            'component_stats': self.component_stats
        }
    
    def generate_report(self, verbose: bool = False) -> str:
        """Generate a comprehensive linting report."""
        report = []
        report.append("\n" + "=" * 60)
        report.append("📊 LINTING REPORT")
        report.append("=" * 60)
        
        # Summary statistics
        stats = self.component_stats
        report.append(f"📁 Files processed: {stats['total_files']}")
        report.append(f"🧩 Components analyzed: {stats['total_components']}")
        report.append(f"✅ Valid components: {stats['valid_components']}")
        report.append(f"❌ Invalid components: {stats['invalid_components']}")
        report.append(f"🔧 Component types found: {len(stats['component_types'])}")
        
        if stats['total_components'] > 0:
            success_rate = (stats['valid_components'] / stats['total_components']) * 100
            report.append(f"📈 Schema compliance: {success_rate:.1f}%")
        
        # Issue summary by severity
        severity_counts = {}
        for issue in self.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        report.append(f"\n📋 Issues by severity:")
        for severity in LintSeverity:
            count = severity_counts.get(severity, 0)
            if count > 0:
                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️", "style": "💄"}[severity.value]
                report.append(f"   {icon} {severity.value}: {count}")
        
        # Issues by component type
        component_issues = {}
        for issue in self.issues:
            comp_type = issue.component_type
            if comp_type not in component_issues:
                component_issues[comp_type] = []
            component_issues[comp_type].append(issue)
        
        if component_issues:
            report.append(f"\n🎯 Issues by component type:")
            for comp_type, issues in sorted(component_issues.items()):
                report.append(f"   {comp_type}: {len(issues)} issues")
        
        # Most common component types
        if stats['component_types']:
            report.append(f"\n🏗️ Component types discovered:")
            for comp_type in sorted(stats['component_types']):
                report.append(f"   - {comp_type}")
        
        # Detailed issues (if verbose or critical errors)
        critical_issues = [i for i in self.issues if i.severity == LintSeverity.ERROR]
        if verbose or critical_issues:
            report.append(f"\n🔍 DETAILED ISSUES")
            report.append("-" * 60)
            
            issues_to_show = self.issues if verbose else critical_issues
            
            # Group issues by file for better readability
            issues_by_file = {}
            for issue in issues_to_show:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)
            
            for file_path, file_issues in issues_by_file.items():
                # Show relative path for readability
                rel_path = os.path.relpath(file_path) if len(file_path) > 80 else file_path
                report.append(f"\n📄 {rel_path}")
                
                for issue in file_issues:
                    severity_icon = {
                        "error": "❌", "warning": "⚠️",
                        "info": "ℹ️", "style": "💄"
                    }[issue.severity.value]
                    
                    report.append(f"   {severity_icon} {issue.code}: {issue.message}")
                    report.append(f"      Component: {issue.component_type} at {issue.component_path}")
                    if issue.suggestion:
                        report.append(f"      Suggestion: {issue.suggestion}")
                    report.append("")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(
        description="Lint Ignition Perspective view.json files for schema compliance and best practices"
    )
    parser.add_argument(
        "--target", "-t",
        required=True,
        help="Path to Ignition project directory or specific view file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output with all issues"
    )
    parser.add_argument(
        "--component-type", "-c",
        help="Filter linting to specific component type (e.g., 'ia.display.label')"
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="Path to component schema file (default: schemas/core-ia-components-schema-robust.json)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output report to file instead of stdout"
    )
    
    args = parser.parse_args()
    
    # Initialize linter
    linter = IgnitionPerspectiveLinter(args.schema)
    
    # Run linting
    result = linter.lint_project(args.target, args.component_type)
    
    if not result['success']:
        print(f"❌ Linting failed: {result['message']}")
        sys.exit(1)
    
    # Generate report
    report = linter.generate_report(args.verbose)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📝 Report saved to: {args.output}")
    else:
        print(report)
    
    # Exit with appropriate code
    critical_issues = len([i for i in linter.issues if i.severity == LintSeverity.ERROR])
    if critical_issues > 0:
        print(f"\n❌ Linting completed with {critical_issues} critical errors")
        sys.exit(1)
    else:
        print(f"\n✅ Linting completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
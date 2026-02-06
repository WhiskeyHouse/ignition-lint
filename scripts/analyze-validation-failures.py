#!/usr/bin/env python3
"""
Analyze validation failures to improve schema robustness
Extract common patterns from failing components to update schema definitions
"""

import json
import os
from collections import defaultdict
from typing import Any

from jsonschema import ValidationError, validate

REPO_PATH = "/Users/pmannion/Documents/whiskeyhouse/whk-distillery01-ignition-global"
VIEWS_PATH = os.path.join(REPO_PATH, "com.inductiveautomation.perspective/views")
SCHEMA_PATH = "./core-ia-components-schema-robust.json"


def load_schema() -> dict:
    """Load the current schema"""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def find_view_files(views_path: str) -> list[str]:
    """Find all view.json files recursively"""
    view_files = []
    for root, _dirs, files in os.walk(views_path):
        for file in files:
            if file == "view.json":
                view_files.append(os.path.join(root, file))
    return view_files


def extract_ia_components(view_data: dict) -> list[dict]:
    """Extract all ia.* components from a view recursively"""
    components = []

    def extract_recursive(obj):
        if isinstance(obj, dict):
            if (
                "type" in obj
                and isinstance(obj["type"], str)
                and obj["type"].startswith("ia.")
            ):
                components.append(obj)
            if "children" in obj and isinstance(obj["children"], list):
                for child in obj["children"]:
                    extract_recursive(child)
            if "root" in obj:
                extract_recursive(obj["root"])

    extract_recursive(view_data)
    return components


def analyze_validation_error(component: dict, schema: dict) -> dict[str, Any]:
    """Analyze a specific validation error in detail"""
    try:
        validate(instance=component, schema=schema)
        return None
    except ValidationError as e:
        return {
            "error_message": e.message,
            "error_path": list(e.absolute_path),
            "schema_path": list(e.schema_path),
            "failing_value": e.instance,
            "expected_schema": e.schema,
            "component": component,
        }


def get_property_at_path(obj: Any, path: list[str]) -> Any:
    """Get property value at a specific path"""
    current = obj
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit():
            idx = int(key)
            if 0 <= idx < len(current):
                current = current[idx]
            else:
                return None
        else:
            return None
    return current


def analyze_type_mismatches():
    """Analyze common type mismatches in the codebase"""
    print("🔍 Analyzing Type Mismatches in Production Codebase")
    print("=" * 60)

    schema = load_schema()
    view_files = find_view_files(VIEWS_PATH)

    # Track validation errors by type
    error_patterns = defaultdict(list)
    property_type_usage = defaultdict(lambda: defaultdict(set))

    total_components = 0
    failing_components = 0

    for view_file in view_files:
        try:
            with open(view_file) as f:
                view_data = json.load(f)

            components = extract_ia_components(view_data)
            total_components += len(components)

            for component in components:
                error_info = analyze_validation_error(component, schema)
                if error_info:
                    failing_components += 1

                    # Extract key information
                    error_msg = error_info["error_message"]
                    path = error_info["error_path"]
                    failing_value = error_info["failing_value"]
                    expected_schema = error_info["expected_schema"]

                    # Categorize error patterns
                    if "is not of type" in error_msg:
                        path_str = ".".join(map(str, path))
                        actual_type = type(failing_value).__name__
                        expected_types = expected_schema.get("type", "unknown")

                        pattern_key = f"{path_str}|{actual_type}→{expected_types}"
                        error_patterns[pattern_key].append(
                            {
                                "value": failing_value,
                                "component_type": component.get("type", "unknown"),
                                "file": view_file,
                            }
                        )

                        # Track actual type usage
                        property_type_usage[path_str][actual_type].add(failing_value)

        except Exception:
            continue

    print("📊 Analysis Results:")
    print(f"   Total components: {total_components}")
    print(f"   Failing components: {failing_components}")
    if total_components > 0:
        print(
            f"   Success rate: {((total_components - failing_components) / total_components * 100):.1f}%"
        )
    else:
        print("   Success rate: N/A (no components found)")

    print("\n🎯 Top Type Mismatch Patterns:")
    print("-" * 60)

    # Sort patterns by frequency
    sorted_patterns = sorted(
        error_patterns.items(), key=lambda x: len(x[1]), reverse=True
    )

    for pattern, occurrences in sorted_patterns[:20]:  # Top 20 patterns
        path, type_mismatch = pattern.split("|")
        actual_type, expected_types = type_mismatch.split("→")

        print(f"\n📍 Property: {path}")
        print(f"   Expected: {expected_types}")
        print(f"   Found: {actual_type} ({len(occurrences)} instances)")

        # Show sample values
        sample_values = list({str(occ["value"])[:50] for occ in occurrences[:5]})
        print(f"   Sample values: {sample_values}")

        # Show component types affected
        comp_types = {occ["component_type"] for occ in occurrences}
        print(f"   Affected components: {sorted(comp_types)}")

    print("\n🔧 Property Type Usage Analysis:")
    print("-" * 60)

    # Analyze properties that have multiple type usage patterns
    for prop_path, type_usage in property_type_usage.items():
        if len(type_usage) > 1:  # Property used with multiple types
            print(f"\n📌 {prop_path}:")
            for data_type, values in type_usage.items():
                unique_vals = list(values)[:5]  # First 5 unique values
                print(f"   {data_type}: {len(values)} unique values - {unique_vals}")

    return error_patterns, property_type_usage


def suggest_schema_improvements(error_patterns: dict, property_type_usage: dict):
    """Generate schema improvement suggestions based on analysis"""
    print("\n💡 Schema Improvement Suggestions:")
    print("=" * 60)

    suggestions = []

    # Analyze properties that need more flexible types
    for prop_path, type_usage in property_type_usage.items():
        if len(type_usage) > 1:
            current_types = list(type_usage.keys())

            # Common patterns that need fixing
            if "int" in current_types and "str" in current_types:
                suggestions.append(
                    {
                        "property": prop_path,
                        "issue": "Numbers and strings both used",
                        "solution": 'Change type to ["number", "string"]',
                        "examples": {
                            t: list(vals)[:3] for t, vals in type_usage.items()
                        },
                    }
                )

            if "dict" in current_types and "str" in current_types:
                suggestions.append(
                    {
                        "property": prop_path,
                        "issue": "Objects and strings both used",
                        "solution": 'Change type to ["object", "string"]',
                        "examples": {
                            t: list(vals)[:3] for t, vals in type_usage.items()
                        },
                    }
                )

            if "list" in current_types and (
                "dict" in current_types or "str" in current_types
            ):
                suggestions.append(
                    {
                        "property": prop_path,
                        "issue": "Arrays mixed with other types",
                        "solution": f"Change type to {current_types}",
                        "examples": {
                            t: list(vals)[:3] for t, vals in type_usage.items()
                        },
                    }
                )

    # Print suggestions
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. Property: {suggestion['property']}")
        print(f"   Issue: {suggestion['issue']}")
        print(f"   Solution: {suggestion['solution']}")
        print("   Examples found:")
        for data_type, examples in suggestion["examples"].items():
            print(f"     {data_type}: {examples}")

    return suggestions


def generate_schema_patch(suggestions: list[dict]) -> dict:
    """Generate a schema patch based on suggestions"""
    print("\n🔨 Generating Schema Patch:")
    print("=" * 60)

    patches = {}

    for suggestion in suggestions:
        prop_path = suggestion["property"]
        examples = suggestion["examples"]

        # Determine appropriate JSON Schema type array
        type_array = []
        if "str" in examples:
            type_array.append("string")
        if "int" in examples or "float" in examples:
            type_array.append("number")
        if "dict" in examples:
            type_array.append("object")
        if "list" in examples:
            type_array.append("array")
        if "bool" in examples:
            type_array.append("boolean")
        if "NoneType" in examples:
            type_array.append("null")

        patches[prop_path] = {
            "type": type_array if len(type_array) > 1 else type_array[0],
            "description": "Flexible type based on production usage analysis",
        }

        print(f"   {prop_path}: {type_array}")

    return patches


def main():
    print("🚀 Schema Improvement Analysis")
    print("Using production codebase:", REPO_PATH)
    print()

    # Run analysis
    error_patterns, property_type_usage = analyze_type_mismatches()

    # Generate suggestions
    suggestions = suggest_schema_improvements(error_patterns, property_type_usage)

    # Generate patch
    patch = generate_schema_patch(suggestions)

    # Save analysis results
    results = {
        "analysis_summary": {
            "error_patterns": len(error_patterns),
            "properties_with_multiple_types": len(
                [p for p, t in property_type_usage.items() if len(t) > 1]
            ),
            "suggestions_generated": len(suggestions),
        },
        "error_patterns": {k: len(v) for k, v in error_patterns.items()},
        "property_type_usage": {
            k: {t: list(v) for t, v in types.items()}
            for k, types in property_type_usage.items()
        },
        "suggestions": suggestions,
        "schema_patches": patch,
    }

    with open("schema_analysis_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("\n📝 Analysis results saved to: schema_analysis_results.json")
    print(f"💡 Generated {len(suggestions)} schema improvement suggestions")
    print(f"🔧 Ready to apply {len(patch)} schema patches")


if __name__ == "__main__":
    main()

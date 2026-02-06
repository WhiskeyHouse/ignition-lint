#!/usr/bin/env python3
"""
Analyze multiple Ignition codebases to refine schema based on broader empirical evidence
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from jsonschema import ValidationError, validate

# Multiple codebase paths
CODEBASES = {
    "whk-distillery01-ignition-global": "/Users/pmannion/Documents/whiskeyhouse/whk-distillery01-ignition-global",
    "whk-ignition-scada": "/Users/pmannion/Documents/whiskeyhouse/whk-ignition-scada",
}

SCHEMA_PATH = "./core-ia-components-schema-robust.json"


def load_schema() -> dict:
    """Load the current schema"""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def find_view_files(base_path: str) -> list[str]:
    """Find all view.json files in a codebase"""
    view_files = []

    if not os.path.exists(base_path):
        print(f"⚠️  Warning: Path does not exist: {base_path}")
        return []

    # Look for perspective views structure
    perspective_path = os.path.join(
        base_path, "com.inductiveautomation.perspective", "views"
    )
    if os.path.exists(perspective_path):
        search_path = perspective_path
    else:
        search_path = base_path

    for root, _dirs, files in os.walk(search_path):
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


def analyze_validation_error(component: dict, schema: dict) -> dict[str, Any] | None:
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


def analyze_codebase(
    codebase_name: str, base_path: str, schema: dict
) -> dict[str, Any]:
    """Analyze a single codebase"""
    print(f"\n📁 Analyzing {codebase_name}")
    print("-" * 50)

    view_files = find_view_files(base_path)

    if not view_files:
        print(f"   No view files found in {base_path}")
        return {
            "codebase": codebase_name,
            "view_files": 0,
            "components": 0,
            "valid_components": 0,
            "component_types": [],
            "error_patterns": {},
            "property_type_usage": {},
        }

    print(f"   Found {len(view_files)} view files")

    # Track validation errors and patterns
    error_patterns = defaultdict(list)
    property_type_usage = defaultdict(lambda: defaultdict(set))
    component_types = set()

    total_components = 0
    valid_components = 0

    for view_file in view_files:
        try:
            with open(view_file, encoding="utf-8") as f:
                view_data = json.load(f)

            components = extract_ia_components(view_data)
            total_components += len(components)

            for component in components:
                comp_type = component.get("type", "unknown")
                component_types.add(comp_type)

                error_info = analyze_validation_error(component, schema)
                if error_info:
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
                                "component_type": comp_type,
                                "file": view_file,
                            }
                        )

                        # Track actual type usage
                        property_type_usage[path_str][actual_type].add(
                            str(failing_value)[:100]
                        )  # Truncate long values
                else:
                    valid_components += 1

        except Exception as e:
            print(f"   Error processing {view_file}: {e}")
            continue

    success_rate = (
        (valid_components / total_components * 100) if total_components > 0 else 0
    )

    print("   📊 Results:")
    print(f"      Components: {total_components}")
    print(f"      Valid: {valid_components} ({success_rate:.1f}%)")
    print(f"      Component types: {len(component_types)}")
    print(f"      Error patterns: {len(error_patterns)}")

    return {
        "codebase": codebase_name,
        "view_files": len(view_files),
        "components": total_components,
        "valid_components": valid_components,
        "success_rate": success_rate,
        "component_types": sorted(component_types),
        "error_patterns": dict(error_patterns),
        "property_type_usage": {
            k: {t: list(v) for t, v in types.items()}
            for k, types in property_type_usage.items()
        },
    }


def compare_codebases(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare results across codebases"""
    print("\n📈 Cross-Codebase Comparison")
    print("=" * 60)

    # Aggregate statistics
    total_files = sum(r["view_files"] for r in results)
    total_components = sum(r["components"] for r in results)
    total_valid = sum(r["valid_components"] for r in results)

    print("📊 Aggregate Statistics:")
    print(f"   Total view files: {total_files}")
    print(f"   Total components: {total_components}")
    success_rate = (total_valid / total_components * 100) if total_components else 0.0
    print(f"   Overall success rate: {success_rate:.1f}%")

    # Component type coverage
    all_component_types = set()
    for result in results:
        all_component_types.update(result["component_types"])

    print(f"   Total unique component types: {len(all_component_types)}")

    # Component type comparison
    print("\n🎯 Component Type Coverage by Codebase:")
    for result in results:
        codebase_types = result["component_types"]
        coverage = len(codebase_types)
        print(f"   {result['codebase']}: {coverage} types")

        # Show types unique to this codebase
        other_types = set()
        for other_result in results:
            if other_result["codebase"] != result["codebase"]:
                other_types.update(other_result["component_types"])

        unique_types = set(codebase_types) - other_types
        if unique_types:
            print(f"      Unique to this codebase: {sorted(unique_types)}")

    # Aggregate error patterns
    all_error_patterns = defaultdict(list)
    for result in results:
        for pattern, occurrences in result["error_patterns"].items():
            all_error_patterns[pattern].extend(occurrences)

    # Show most common error patterns across codebases
    if all_error_patterns:
        print("\n🔍 Most Common Error Patterns Across All Codebases:")
        sorted_patterns = sorted(
            all_error_patterns.items(), key=lambda x: len(x[1]), reverse=True
        )

        for pattern, occurrences in sorted_patterns[:10]:
            path, type_mismatch = pattern.split("|")
            actual_type, expected_types = type_mismatch.split("→")

            # Count by codebase
            codebase_counts = Counter(
                occ.get("file", "").split("/")[-4] for occ in occurrences
            )

            print(
                f"   📍 {path}: {actual_type} → {expected_types} ({len(occurrences)} total)"
            )
            for codebase, count in codebase_counts.most_common():
                if codebase:  # Skip empty codebase names
                    print(f"      {codebase}: {count} instances")

    return {
        "total_files": total_files,
        "total_components": total_components,
        "total_valid": total_valid,
        "overall_success_rate": total_valid / total_components * 100
        if total_components > 0
        else 0,
        "all_component_types": sorted(all_component_types),
        "aggregated_error_patterns": dict(all_error_patterns),
    }


def suggest_schema_improvements_from_multi_codebase(
    aggregated_results: dict[str, Any],
) -> list[dict]:
    """Generate schema improvement suggestions from multiple codebases"""
    print("\n💡 Multi-Codebase Schema Improvement Suggestions:")
    print("=" * 60)

    suggestions = []
    error_patterns = aggregated_results["aggregated_error_patterns"]

    # Look for patterns that appear across multiple codebases
    for pattern, occurrences in error_patterns.items():
        if len(occurrences) >= 2:  # At least 2 instances across codebases
            path, type_mismatch = pattern.split("|")
            actual_type, expected_types = type_mismatch.split("→")

            # Check if it appears in multiple codebases
            codebases_affected = set()
            for occ in occurrences:
                file_path = occ.get("file", "")
                if "whk-distillery01" in file_path:
                    codebases_affected.add("distillery")
                elif "whk-ignition-scada" in file_path:
                    codebases_affected.add("scada")

            if len(codebases_affected) > 1:  # Cross-codebase pattern
                suggestions.append(
                    {
                        "property": path,
                        "current_type": expected_types,
                        "needed_type": actual_type,
                        "occurrences": len(occurrences),
                        "codebases": list(codebases_affected),
                        "priority": "HIGH",
                        "reason": f"Pattern appears across {len(codebases_affected)} codebases",
                    }
                )
            elif len(occurrences) >= 5:  # High frequency in single codebase
                suggestions.append(
                    {
                        "property": path,
                        "current_type": expected_types,
                        "needed_type": actual_type,
                        "occurrences": len(occurrences),
                        "codebases": list(codebases_affected),
                        "priority": "MEDIUM",
                        "reason": f"High frequency pattern ({len(occurrences)} instances)",
                    }
                )

    # Sort by priority and frequency
    suggestions.sort(
        key=lambda x: (x["priority"] == "HIGH", x["occurrences"]), reverse=True
    )

    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. Property: {suggestion['property']}")
        print(f"   Current schema: {suggestion['current_type']}")
        print(f"   Needs to support: {suggestion['needed_type']}")
        print(f"   Frequency: {suggestion['occurrences']} instances")
        print(f"   Codebases: {', '.join(suggestion['codebases'])}")
        print(f"   Priority: {suggestion['priority']}")
        print(f"   Reason: {suggestion['reason']}")

    return suggestions


def main():
    print("🚀 Multi-Codebase Schema Analysis")
    print("Comparing empirical evidence across Ignition codebases")
    print("=" * 60)

    schema = load_schema()
    results = []

    # Analyze each codebase
    for codebase_name, base_path in CODEBASES.items():
        result = analyze_codebase(codebase_name, base_path, schema)
        results.append(result)

    # Compare results
    aggregated = compare_codebases(results)

    # Generate improvement suggestions
    suggestions = suggest_schema_improvements_from_multi_codebase(aggregated)

    # Save comprehensive results
    analysis_results = {
        "analysis_date": datetime.now(timezone.utc)
        .date()
        .isoformat(),  # generated at runtime
        "schema_version": "robust",
        "codebases_analyzed": list(CODEBASES.keys()),
        "individual_results": results,
        "aggregated_results": aggregated,
        "improvement_suggestions": suggestions,
    }

    output_file = "multi_codebase_analysis_results.json"
    with open(output_file, "w") as f:
        json.dump(analysis_results, f, indent=2, default=str)

    print(f"\n📝 Complete analysis saved to: {output_file}")
    print(f"💡 Generated {len(suggestions)} cross-codebase improvement suggestions")

    if suggestions:
        high_priority = [s for s in suggestions if s["priority"] == "HIGH"]
        print(
            f"🔥 {len(high_priority)} HIGH PRIORITY suggestions need immediate attention"
        )


if __name__ == "__main__":
    main()

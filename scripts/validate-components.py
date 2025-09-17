#!/usr/bin/env python3
"""
Validation script for Ignition Perspective Core Components
Tests the generated schemas against actual components in the repository
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import jsonschema
from jsonschema import validate, ValidationError

# Path to the whk-distillery01-ignition-global repo
REPO_PATH = "/Users/pmannion/Documents/whiskeyhouse/whk-distillery01-ignition-global"
VIEWS_PATH = os.path.join(REPO_PATH, "com.inductiveautomation.perspective/views")
# Get schema path relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "schemas", "core-ia-components-schema-robust.json")

def load_schema() -> dict:
    """Load the JSON schema for validation"""
    try:
        with open(SCHEMA_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found at {SCHEMA_PATH}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e}")
        sys.exit(1)

def find_view_files(views_path: str) -> List[str]:
    """Find all view.json files recursively"""
    view_files = []
    for root, dirs, files in os.walk(views_path):
        for file in files:
            if file == "view.json":
                view_files.append(os.path.join(root, file))
    return view_files

def extract_ia_components(view_data: dict) -> List[dict]:
    """Extract all ia.* components from a view recursively"""
    components = []
    
    def extract_recursive(obj):
        if isinstance(obj, dict):
            if 'type' in obj and isinstance(obj['type'], str) and obj['type'].startswith('ia.'):
                components.append(obj)
            if 'children' in obj and isinstance(obj['children'], list):
                for child in obj['children']:
                    extract_recursive(child)
            if 'root' in obj:
                extract_recursive(obj['root'])
    
    extract_recursive(view_data)
    return components

def validate_component(component: dict, schema: dict) -> Tuple[bool, str]:
    """Validate a single component against the schema"""
    try:
        validate(instance=component, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, str(e)

def analyze_component_usage(components: List[dict]) -> Dict[str, int]:
    """Analyze component type usage statistics"""
    usage = {}
    for component in components:
        comp_type = component.get('type', 'unknown')
        usage[comp_type] = usage.get(comp_type, 0) + 1
    return usage

def main():
    print("🔍 Ignition Perspective Component Validator")
    print("=" * 50)
    
    # Load schema
    print("📋 Loading schema...")
    schema = load_schema()
    print(f"✅ Schema loaded successfully")
    
    # Find view files
    print(f"\n🔎 Searching for view files in {VIEWS_PATH}...")
    view_files = find_view_files(VIEWS_PATH)
    print(f"✅ Found {len(view_files)} view files")
    
    # Process all views
    all_components = []
    total_views = 0
    failed_views = []
    
    print(f"\n📊 Processing views...")
    for view_file in view_files:
        try:
            with open(view_file, 'r') as f:
                view_data = json.load(f)
            
            components = extract_ia_components(view_data)
            all_components.extend(components)
            total_views += 1
            
            if total_views % 50 == 0:
                print(f"   Processed {total_views} views, found {len(all_components)} components...")
                
        except Exception as e:
            failed_views.append((view_file, str(e)))
    
    print(f"✅ Processed {total_views} views successfully")
    if failed_views:
        print(f"⚠️  Failed to process {len(failed_views)} views")
    
    # Analyze component usage
    print(f"\n📈 Component usage analysis:")
    usage_stats = analyze_component_usage(all_components)
    
    # Sort by usage count
    sorted_usage = sorted(usage_stats.items(), key=lambda x: x[1], reverse=True)
    
    print(f"   Total unique component types: {len(sorted_usage)}")
    print(f"   Total component instances: {len(all_components)}")
    print(f"\n   Top 10 most used components:")
    for comp_type, count in sorted_usage[:10]:
        percentage = (count / len(all_components)) * 100
        print(f"   - {comp_type}: {count} ({percentage:.1f}%)")
    
    # Validate components
    print(f"\n🧪 Validating components against schema...")
    valid_count = 0
    invalid_count = 0
    validation_errors = {}
    
    for i, component in enumerate(all_components):
        is_valid, error_msg = validate_component(component, schema)
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            comp_type = component.get('type', 'unknown')
            if comp_type not in validation_errors:
                validation_errors[comp_type] = []
            validation_errors[comp_type].append(error_msg)
        
        if (i + 1) % 100 == 0:
            print(f"   Validated {i + 1}/{len(all_components)} components...")
    
    # Results
    print(f"\n📊 Validation Results:")
    print(f"   ✅ Valid components: {valid_count}")
    print(f"   ❌ Invalid components: {invalid_count}")
    
    if validation_errors:
        print(f"\n🚨 Validation errors by component type:")
        for comp_type, errors in validation_errors.items():
            print(f"   - {comp_type}: {len(errors)} errors")
            # Show first few unique errors
            unique_errors = list(set(errors))[:3]
            for error in unique_errors:
                # Truncate long error messages
                error_preview = error[:100] + "..." if len(error) > 100 else error
                print(f"     • {error_preview}")
    
    # Component type coverage
    print(f"\n🎯 Schema coverage analysis:")
    expected_types = {
        'ia.container.flex', 'ia.container.coord', 'ia.container.breakpt', 'ia.container.tab',
        'ia.display.label', 'ia.display.icon', 'ia.display.view', 'ia.display.table',
        'ia.display.flex-repeater', 'ia.display.markdown', 'ia.display.tree', 'ia.display.image',
        'ia.display.iframe', 'ia.display.tag-browse-tree', 'ia.display.viewcanvas',
        'ia.display.progress', 'ia.display.equipmentschedule', 'ia.display.barcode',
        'ia.display.alarmstatustable', 'ia.display.alarmjournaltable',
        'ia.input.button', 'ia.input.dropdown', 'ia.input.text-field', 'ia.input.numeric-entry-field',
        'ia.input.checkbox', 'ia.input.text-area', 'ia.input.oneshotbutton', 'ia.input.date-time-input',
        'ia.input.multi-state-button', 'ia.input.toggle-switch', 'ia.input.signature-pad',
        'ia.input.fileupload', 'ia.chart.pie', 'ia.chart.xy',
        'ia.navigation.menutree', 'ia.navigation.horizontalmenu'
    }
    
    found_types = set(comp_type for comp_type in usage_stats.keys() if comp_type.startswith('ia.'))
    
    covered_types = expected_types & found_types
    missing_types = expected_types - found_types
    unexpected_types = found_types - expected_types
    
    print(f"   Expected component types: {len(expected_types)}")
    print(f"   Found component types: {len(found_types)}")
    print(f"   Coverage: {len(covered_types)}/{len(expected_types)} ({(len(covered_types)/len(expected_types)*100):.1f}%)")
    
    if missing_types:
        print(f"   📭 Missing types (not found in views): {sorted(missing_types)}")
    
    if unexpected_types:
        print(f"   🆕 Unexpected types (found but not in schema): {sorted(unexpected_types)}")
    
    # Summary
    success_rate = (valid_count / len(all_components)) * 100 if all_components else 0
    print(f"\n🎉 Summary:")
    print(f"   Overall validation success rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("   🎯 Excellent! Schema covers most use cases.")
    elif success_rate >= 70:
        print("   👍 Good coverage, but some refinement needed.")
    else:
        print("   ⚠️  Schema needs significant improvement.")
    
    return success_rate >= 70

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Detailed component inspector - examines individual components against schema
to identify specific validation issues and schema robustness gaps
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set
import jsonschema
from jsonschema import validate, ValidationError

REPO_PATH = "/Users/pmannion/Documents/whiskeyhouse/whk-distillery01-ignition-global"
VIEWS_PATH = os.path.join(REPO_PATH, "com.inductiveautomation.perspective/views")

def load_schemas():
    """Load both schemas for comparison"""
    schemas = {}
    for schema_name in ["core-ia-components-schema-permissive.json", "core-ia-components-schema.json"]:
        try:
            with open(schema_name, 'r') as f:
                schemas[schema_name] = json.load(f)
        except FileNotFoundError:
            print(f"Warning: {schema_name} not found")
    return schemas

def find_view_files(views_path: str) -> List[str]:
    """Find all view.json files recursively"""
    view_files = []
    for root, dirs, files in os.walk(views_path):
        for file in files:
            if file == "view.json":
                view_files.append(os.path.join(root, file))
    return view_files

def extract_ia_components_with_source(view_data: dict, source_file: str) -> List[tuple]:
    """Extract all ia.* components with their source file info"""
    components = []
    
    def extract_recursive(obj, path="root"):
        if isinstance(obj, dict):
            if 'type' in obj and isinstance(obj['type'], str) and obj['type'].startswith('ia.'):
                components.append((obj, source_file, path))
            if 'children' in obj and isinstance(obj['children'], list):
                for i, child in enumerate(obj['children']):
                    extract_recursive(child, f"{path}.children[{i}]")
            if 'root' in obj:
                extract_recursive(obj['root'], f"{path}.root")
    
    extract_recursive(view_data)
    return components

def validate_component_detailed(component: dict, schema: dict, schema_name: str) -> Dict:
    """Detailed validation of a single component"""
    result = {
        'valid': False,
        'schema': schema_name,
        'component_type': component.get('type', 'unknown'),
        'errors': [],
        'warnings': [],
        'missing_properties': [],
        'unexpected_properties': []
    }
    
    try:
        validate(instance=component, schema=schema)
        result['valid'] = True
    except ValidationError as e:
        result['valid'] = False
        result['errors'].append({
            'message': e.message,
            'path': list(e.absolute_path),
            'schema_path': list(e.schema_path)
        })
    
    return result

def analyze_component_structure(component: dict) -> Dict:
    """Analyze the structure of a component for insights"""
    analysis = {
        'has_meta': 'meta' in component,
        'has_props': 'props' in component,
        'has_position': 'position' in component,
        'has_events': 'events' in component,
        'has_children': 'children' in component and len(component.get('children', [])) > 0,
        'has_propConfig': 'propConfig' in component,
        'has_custom': 'custom' in component,
        'top_level_properties': list(component.keys()),
        'props_properties': list(component.get('props', {}).keys()),
        'position_properties': list(component.get('position', {}).keys()),
        'meta_properties': list(component.get('meta', {}).keys())
    }
    return analysis

def main():
    print("🔍 Detailed Component Inspector")
    print("=" * 50)
    
    # Load schemas
    schemas = load_schemas()
    if not schemas:
        print("No schemas found!")
        return
    
    print(f"Loaded {len(schemas)} schemas: {list(schemas.keys())}")
    
    # Find view files
    view_files = find_view_files(VIEWS_PATH)
    print(f"Found {len(view_files)} view files")
    
    # Process components
    all_components = []
    for view_file in view_files:
        try:
            with open(view_file, 'r') as f:
                view_data = json.load(f)
            components = extract_ia_components_with_source(view_data, view_file)
            all_components.extend(components)
        except Exception as e:
            print(f"Error processing {view_file}: {e}")
    
    print(f"Found {len(all_components)} total components")
    
    # Sample detailed inspection of first 10 components of each type
    component_types = {}
    for component, source_file, path in all_components:
        comp_type = component.get('type', 'unknown')
        if comp_type not in component_types:
            component_types[comp_type] = []
        if len(component_types[comp_type]) < 3:  # Keep first 3 of each type for detailed analysis
            component_types[comp_type].append((component, source_file, path))
    
    print(f"\n🧪 Detailed Analysis of Sample Components")
    print("=" * 50)
    
    for comp_type, samples in component_types.items():
        print(f"\n📋 Component Type: {comp_type}")
        print(f"   Analyzing {len(samples)} samples...")
        
        for i, (component, source_file, path) in enumerate(samples):
            print(f"\n   Sample {i+1}:")
            print(f"   Source: {source_file}")
            print(f"   Path: {path}")
            
            # Analyze structure
            structure = analyze_component_structure(component)
            print(f"   Structure:")
            print(f"     - Top-level properties: {structure['top_level_properties']}")
            if structure['has_props']:
                print(f"     - Props properties: {structure['props_properties'][:10]}...")  # Truncate if long
            if structure['has_position']:
                print(f"     - Position properties: {structure['position_properties']}")
            
            # Test against schemas
            for schema_name, schema in schemas.items():
                validation_result = validate_component_detailed(component, schema, schema_name)
                status = "✅" if validation_result['valid'] else "❌"
                print(f"     - {schema_name}: {status}")
                
                if not validation_result['valid']:
                    for error in validation_result['errors']:
                        print(f"       Error: {error['message']}")
                        if error['path']:
                            print(f"       At path: {'.'.join(map(str, error['path']))}")
            
            # Show actual component structure (truncated)
            component_preview = json.dumps(component, indent=2)[:500]
            print(f"   Component preview:")
            for line in component_preview.split('\n')[:10]:
                print(f"     {line}")
            if len(component_preview) > 500:
                print("     ... (truncated)")
    
    # Identify patterns in failures
    print(f"\n🎯 Pattern Analysis")
    print("=" * 50)
    
    # Look for properties that might be missing from schemas
    all_properties = set()
    property_usage = {}
    
    for component, _, _ in all_components:
        comp_type = component.get('type', 'unknown')
        
        # Collect all properties used
        for key in component.keys():
            prop_name = f"root.{key}"
            all_properties.add(prop_name)
            if prop_name not in property_usage:
                property_usage[prop_name] = set()
            property_usage[prop_name].add(comp_type)
        
        # Props properties
        for key in component.get('props', {}).keys():
            prop_name = f"props.{key}"
            all_properties.add(prop_name)
            if prop_name not in property_usage:
                property_usage[prop_name] = set()
            property_usage[prop_name].add(comp_type)
            
        # Position properties
        for key in component.get('position', {}).keys():
            prop_name = f"position.{key}"
            all_properties.add(prop_name)
            if prop_name not in property_usage:
                property_usage[prop_name] = set()
            property_usage[prop_name].add(comp_type)
    
    print(f"Total unique properties found: {len(all_properties)}")
    print(f"\nMost common properties across all components:")
    sorted_props = sorted(property_usage.items(), key=lambda x: len(x[1]), reverse=True)
    for prop, comp_types in sorted_props[:20]:
        print(f"  - {prop}: used by {len(comp_types)} component types")
    
    print(f"\nUnusual properties (used by only 1 component type):")
    unusual_props = [(prop, list(comp_types)[0]) for prop, comp_types in property_usage.items() if len(comp_types) == 1]
    for prop, comp_type in unusual_props[:10]:
        print(f"  - {prop}: only used by {comp_type}")

if __name__ == "__main__":
    main()
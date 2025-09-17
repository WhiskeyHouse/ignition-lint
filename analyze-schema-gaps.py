#!/usr/bin/env python3
"""
Analyze schema validation gaps to identify missing properties
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set

REPO_PATH = "/Users/pmannion/Documents/whiskeyhouse/whk-distillery01-ignition-global"
VIEWS_PATH = os.path.join(REPO_PATH, "com.inductiveautomation.perspective/views")

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

def analyze_properties(components: List[dict]) -> Dict[str, Dict[str, int]]:
    """Analyze property usage across components"""
    analysis = defaultdict(lambda: defaultdict(int))
    
    for component in components:
        comp_type = component.get('type', 'unknown')
        
        # Analyze top-level properties
        for prop in component.keys():
            if prop != 'type':
                analysis[comp_type][f"root.{prop}"] += 1
        
        # Analyze props properties
        props = component.get('props', {})
        for prop_key in props.keys():
            analysis[comp_type][f"props.{prop_key}"] += 1
            
            # Dive into nested objects
            if isinstance(props[prop_key], dict):
                for nested_key in props[prop_key].keys():
                    analysis[comp_type][f"props.{prop_key}.{nested_key}"] += 1
        
        # Analyze position properties
        position = component.get('position', {})
        for pos_key in position.keys():
            analysis[comp_type][f"position.{pos_key}"] += 1
        
        # Analyze meta properties
        meta = component.get('meta', {})
        for meta_key in meta.keys():
            analysis[comp_type][f"meta.{meta_key}"] += 1
            
        # Analyze events
        events = component.get('events', {})
        for event_type in events.keys():
            analysis[comp_type][f"events.{event_type}"] += 1
            for event_name in events[event_type].keys():
                analysis[comp_type][f"events.{event_type}.{event_name}"] += 1
    
    return dict(analysis)

def main():
    print("🔍 Schema Gap Analysis")
    print("=" * 50)
    
    # Find and process view files
    view_files = find_view_files(VIEWS_PATH)
    print(f"Found {len(view_files)} view files")
    
    all_components = []
    for view_file in view_files:
        try:
            with open(view_file, 'r') as f:
                view_data = json.load(f)
            components = extract_ia_components(view_data)
            all_components.extend(components)
        except Exception as e:
            continue
    
    print(f"Found {len(all_components)} total components")
    
    # Analyze properties
    analysis = analyze_properties(all_components)
    
    # Focus on the most problematic component types
    problem_types = [
        'ia.display.label',
        'ia.input.button', 
        'ia.display.icon',
        'ia.container.flex'
    ]
    
    for comp_type in problem_types:
        if comp_type in analysis:
            print(f"\n📊 Properties for {comp_type}:")
            sorted_props = sorted(analysis[comp_type].items(), 
                                key=lambda x: x[1], reverse=True)
            
            print("   Most common properties:")
            for prop, count in sorted_props[:20]:  # Top 20
                percentage = (count / len([c for c in all_components if c.get('type') == comp_type])) * 100
                print(f"   - {prop}: {count} ({percentage:.1f}%)")
    
    # Look for common patterns across all components
    all_properties = Counter()
    for comp_type, props in analysis.items():
        for prop, count in props.items():
            all_properties[prop] += count
    
    print(f"\n🌟 Most common properties across all components:")
    for prop, count in all_properties.most_common(30):
        print(f"   - {prop}: {count}")

if __name__ == "__main__":
    main()
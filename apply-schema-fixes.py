#!/usr/bin/env python3
"""
Apply targeted schema fixes based on production codebase analysis
"""

import json
import shutil
from datetime import datetime

def backup_schema():
    """Create backup of current schema"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"core-ia-components-schema-robust.json.backup.{timestamp}"
    shutil.copy("core-ia-components-schema-robust.json", backup_path)
    print(f"📋 Schema backed up to: {backup_path}")
    return backup_path

def apply_targeted_fixes():
    """Apply specific fixes based on analysis results"""
    print("🔧 Applying Targeted Schema Fixes")
    print("=" * 50)
    
    # Load current schema
    with open("core-ia-components-schema-robust.json", 'r') as f:
        schema = json.load(f)
    
    fixes_applied = []
    
    # Fix 1: fontSize can be number or string
    if 'properties' in schema and 'props' in schema['properties']:
        props = schema['properties']['props']['properties']
        
        # Fix textStyle.fontSize
        if 'textStyle' in props and 'properties' in props['textStyle']:
            textStyle = props['textStyle']['properties']
            if 'fontSize' in textStyle:
                old_type = textStyle['fontSize'].get('type', 'unknown')
                textStyle['fontSize']['type'] = ['string', 'number']
                fixes_applied.append(f"textStyle.fontSize: {old_type} → ['string', 'number']")
    
    # Fix 2: placeholder can be object or string  
    if 'properties' in schema and 'props' in schema['properties']:
        props = schema['properties']['props']['properties']
        if 'placeholder' in props:
            old_type = props['placeholder'].get('type', 'unknown')
            props['placeholder']['type'] = ['string', 'object']
            fixes_applied.append(f"placeholder: {old_type} → ['string', 'object']")
    
    # Fix 3: wrap can be boolean or string
    if 'properties' in schema and 'props' in schema['properties']:
        props = schema['properties']['props']['properties']
        if 'wrap' in props:
            old_type = props['wrap'].get('type', 'unknown')
            props['wrap']['type'] = ['string', 'boolean']
            fixes_applied.append(f"wrap: {old_type} → ['string', 'boolean']")
    
    # Fix 4: position.grow can be string or number (for cases like ".2")
    if 'properties' in schema and 'position' in schema['properties']:
        position = schema['properties']['position']['properties']
        if 'grow' in position:
            old_type = position['grow'].get('type', 'unknown')
            position['grow']['type'] = ['number', 'string']
            fixes_applied.append(f"position.grow: {old_type} → ['number', 'string']")
    
    # Fix 5: events can have array values (for multiple event handlers)
    if 'properties' in schema and 'events' in schema['properties']:
        events = schema['properties']['events']['properties']
        
        # Update both component and dom events to allow arrays
        for event_type in ['component', 'dom']:
            if event_type in events and 'patternProperties' in events[event_type]:
                pattern_props = events[event_type]['patternProperties']
                for pattern_key in pattern_props:
                    if 'type' in pattern_props[pattern_key]:
                        old_type = pattern_props[pattern_key]['type']
                        pattern_props[pattern_key]['type'] = ['object', 'array']
                        fixes_applied.append(f"events.{event_type}.*: {old_type} → ['object', 'array']")
    
    # Fix 6: style.classes can be object or string (for complex styling)
    if 'properties' in schema and 'props' in schema['properties']:
        props = schema['properties']['props']['properties']
        if 'style' in props and 'properties' in props['style']:
            style = props['style']['properties']
            if 'classes' in style:
                old_type = style['classes'].get('type', 'unknown')
                style['classes']['type'] = ['string', 'object']
                fixes_applied.append(f"style.classes: {old_type} → ['string', 'object']")
    
    return schema, fixes_applied

def validate_fixed_schema():
    """Basic validation that the schema is still valid JSON Schema"""
    try:
        with open("core-ia-components-schema-robust.json", 'r') as f:
            schema = json.load(f)
        
        # Basic checks
        required_keys = ['$schema', 'title', 'type', 'properties']
        for key in required_keys:
            if key not in schema:
                raise ValueError(f"Missing required key: {key}")
        
        print("✅ Schema validation passed")
        return True
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False

def main():
    print("🚀 Applying Production-Driven Schema Fixes")
    print("Based on analysis of whk-distillery01-ignition-global codebase")
    print()
    
    # Create backup
    backup_path = backup_schema()
    
    # Apply fixes
    try:
        schema, fixes_applied = apply_targeted_fixes()
        
        # Save updated schema
        with open("core-ia-components-schema-robust.json", 'w') as f:
            json.dump(schema, f, indent=2)
        
        print(f"✅ Applied {len(fixes_applied)} schema fixes:")
        for fix in fixes_applied:
            print(f"   • {fix}")
        
        # Validate the fixed schema
        if validate_fixed_schema():
            print(f"\n🎉 Schema successfully updated!")
            print(f"📋 Backup available at: {backup_path}")
            print(f"🧪 Run validation again to test improvements")
        else:
            # Restore backup if validation fails
            shutil.copy(backup_path, "core-ia-components-schema-robust.json")
            print(f"❌ Schema validation failed - restored from backup")
            
    except Exception as e:
        # Restore backup on any error
        shutil.copy(backup_path, "core-ia-components-schema-robust.json")
        print(f"❌ Error applying fixes: {e}")
        print(f"📋 Schema restored from backup")

if __name__ == "__main__":
    main()
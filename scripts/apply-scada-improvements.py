#!/usr/bin/env python3
"""
Apply schema improvements based on SCADA codebase analysis
"""

import json
import shutil
from datetime import datetime

def backup_schema():
    """Create backup of current schema"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"core-ia-components-schema-robust.json.backup.scada.{timestamp}"
    shutil.copy("core-ia-components-schema-robust.json", backup_path)
    print(f"📋 Schema backed up to: {backup_path}")
    return backup_path

def apply_scada_improvements():
    """Apply improvements based on SCADA codebase analysis"""
    print("🔧 Applying SCADA Codebase Improvements")
    print("=" * 50)
    
    # Load current schema
    with open("core-ia-components-schema-robust.json", 'r') as f:
        schema = json.load(f)
    
    improvements_applied = []
    
    # 1. Add new component types discovered in SCADA
    new_component_types = [
        "ia.chart.gauge",
        "ia.chart.powerchart", 
        "ia.chart.timeseries",
        "ia.container.column",
        "ia.display.carousel",
        "ia.display.led-display",
        "ia.display.moving-analog-indicator",
        "ia.display.video-player",
        "ia.input.radio-group",
        "ia.shapes.svg",
        "ia.symbol.sensor",
        "ia.symbol.valve"
    ]
    
    current_enum = schema['properties']['type']['enum']
    added_types = []
    
    for new_type in new_component_types:
        if new_type not in current_enum:
            current_enum.append(new_type)
            added_types.append(new_type)
    
    if added_types:
        # Sort the enum for better organization
        schema['properties']['type']['enum'] = sorted(current_enum)
        improvements_applied.append(f"Added {len(added_types)} new component types: {added_types}")
    
    # 2. Fix position properties to allow strings for decimal values
    position_props = schema['properties']['position']['properties']
    
    # width and height can be strings (like ".0404")
    for prop in ['width', 'height', 'x', 'y']:
        if prop in position_props:
            current_type = position_props[prop].get('type', 'number')
            if current_type == 'number':
                position_props[prop]['type'] = ['number', 'string']
                improvements_applied.append(f"position.{prop}: number → ['number', 'string']")
    
    # 3. Fix text properties to allow null values
    text_properties = ['text']
    for prop in text_properties:
        if prop in schema['properties']['props']['properties']:
            current_type = schema['properties']['props']['properties'][prop].get('type', 'string')
            if isinstance(current_type, str) and current_type == 'string':
                schema['properties']['props']['properties'][prop]['type'] = ['string', 'null']
                improvements_applied.append(f"props.{prop}: string → ['string', 'null']")
    
    # 4. Fix meta.visible to allow multiple types
    meta_props = schema['properties']['meta']['properties']
    if 'visible' not in meta_props:
        meta_props['visible'] = {'type': ['boolean', 'string', 'number']}
        improvements_applied.append("Added meta.visible: ['boolean', 'string', 'number']")
    else:
        current_type = meta_props['visible'].get('type', 'boolean')
        if current_type == 'boolean':
            meta_props['visible']['type'] = ['boolean', 'string', 'number']
            improvements_applied.append("meta.visible: boolean → ['boolean', 'string', 'number']")
    
    return schema, improvements_applied

def validate_schema_with_scada():
    """Run quick validation against both codebases"""
    print("\n🧪 Quick Validation Check...")
    
    # Import our validation function
    import subprocess
    
    try:
        result = subprocess.run([
            'uv', 'run', 'python', 'validate-components.py'
        ], capture_output=True, text=True, timeout=60)
        
        output_lines = result.stdout.split('\n')
        
        # Extract key metrics
        for line in output_lines:
            if 'Overall validation success rate:' in line:
                success_rate = line.split(':')[1].strip()
                print(f"   Validation success rate: {success_rate}")
                break
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"   Validation check failed: {e}")
        return False

def main():
    print("🚀 Applying SCADA Codebase Improvements")
    print("Based on analysis of whk-ignition-scada + whk-distillery01-ignition-global")
    print()
    
    # Create backup
    backup_path = backup_schema()
    
    try:
        # Apply improvements
        schema, improvements = apply_scada_improvements()
        
        # Save updated schema
        with open("core-ia-components-schema-robust.json", 'w') as f:
            json.dump(schema, f, indent=2)
        
        print(f"✅ Applied {len(improvements)} improvements:")
        for improvement in improvements:
            print(f"   • {improvement}")
        
        # Quick validation
        if validate_schema_with_scada():
            print(f"\n🎉 Schema successfully updated and validated!")
            print(f"📋 Backup available at: {backup_path}")
        else:
            print(f"\n⚠️  Schema updated but validation had issues")
            print(f"📋 Backup available at: {backup_path}")
            
    except Exception as e:
        # Restore backup on error
        shutil.copy(backup_path, "core-ia-components-schema-robust.json")
        print(f"❌ Error applying improvements: {e}")
        print(f"📋 Schema restored from backup")

if __name__ == "__main__":
    main()
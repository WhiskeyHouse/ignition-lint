#!/usr/bin/env python3
"""
Apply final fixes for remaining edge cases
"""

import json
import shutil
from datetime import datetime


def backup_schema():
    """Create backup of current schema"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"core-ia-components-schema-robust.json.backup.final.{timestamp}"
    shutil.copy("core-ia-components-schema-robust.json", backup_path)
    print(f"📋 Schema backed up to: {backup_path}")
    return backup_path


def apply_final_fixes():
    """Apply final fixes for remaining edge cases"""
    print("🔧 Applying Final Edge Case Fixes")
    print("=" * 50)

    # Load current schema
    with open("core-ia-components-schema-robust.json") as f:
        schema = json.load(f)

    fixes_applied = []

    # 1. Fix position.shrink to allow "Auto" string
    position_props = schema["properties"]["position"]["properties"]
    if "shrink" in position_props:
        current_type = position_props["shrink"].get("type", ["number", "string"])
        if isinstance(current_type, list) and "string" not in current_type:
            position_props["shrink"]["type"] = ["number", "string"]
            fixes_applied.append("position.shrink: number → ['number', 'string']")
        elif current_type == "number":
            position_props["shrink"]["type"] = ["number", "string"]
            fixes_applied.append("position.shrink: number → ['number', 'string']")

    # 2. Fix props.text to allow numbers (for numeric text labels)
    props = schema["properties"]["props"]["properties"]
    if "text" in props:
        current_type = props["text"].get("type", ["string", "null"])
        if isinstance(current_type, str):
            current_type = [current_type]
        if "number" not in current_type:
            props["text"]["type"] = current_type + ["number"]
            fixes_applied.append(
                f"props.text: {current_type} → {current_type + ['number']}"
            )

    # 3. Fix meta.visible to allow null values
    meta_props = schema["properties"]["meta"]["properties"]
    if "visible" in meta_props:
        current_type = meta_props["visible"].get(
            "type", ["boolean", "string", "number"]
        )
        if isinstance(current_type, str):
            current_type = [current_type]
        if "null" not in current_type:
            meta_props["visible"]["type"] = current_type + ["null"]
            fixes_applied.append(
                f"meta.visible: {current_type} → {current_type + ['null']}"
            )

    return schema, fixes_applied


def main():
    print("🚀 Applying Final Schema Fixes")
    print("Addressing remaining edge cases from multi-codebase analysis")
    print()

    # Create backup
    backup_path = backup_schema()

    try:
        # Apply fixes
        schema, fixes = apply_final_fixes()

        # Save updated schema
        with open("core-ia-components-schema-robust.json", "w") as f:
            json.dump(schema, f, indent=2)

        print(f"✅ Applied {len(fixes)} final fixes:")
        for fix in fixes:
            print(f"   • {fix}")

        print("\n🎉 Final schema optimizations complete!")
        print(f"📋 Backup available at: {backup_path}")
        print("🧪 Run multi-codebase analysis to verify improvements")

    except Exception as e:
        # Restore backup on error
        shutil.copy(backup_path, "core-ia-components-schema-robust.json")
        print(f"❌ Error applying fixes: {e}")
        print("📋 Schema restored from backup")


if __name__ == "__main__":
    main()

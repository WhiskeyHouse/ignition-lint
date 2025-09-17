# Ignition Perspective Linter Usage Guide

## Overview

The `ignition-perspective-linter.py` is a robust Python tool that validates Ignition Perspective view.json files against empirical schemas and best practices. It provides comprehensive analysis of component structure, compliance, and code quality.

## Quick Start

```bash
# Basic linting of entire project
uv run python ignition-perspective-linter.py --target /path/to/ignition/project

# Verbose output with all issues
uv run python ignition-perspective-linter.py --target /path/to/ignition/project --verbose

# Filter by component type
uv run python ignition-perspective-linter.py --target /path/to/ignition/project --component-type ia.display.label

# Save report to file
uv run python ignition-perspective-linter.py --target /path/to/ignition/project --output report.txt
```

## Command Line Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--target` | `-t` | **Required.** Path to Ignition project or view file | `/path/to/project` |
| `--verbose` | `-v` | Show detailed output with all issues | `--verbose` |
| `--component-type` | `-c` | Filter to specific component type | `--component-type ia.display.label` |
| `--schema` | | Custom schema file path | `--schema my-schema.json` |
| `--output` | `-o` | Save report to file | `--output report.txt` |

## Issue Severity Levels

### ❌ ERROR (Critical)
- **Schema validation failures** - Component structure doesn't match expected schema
- **Missing required properties** - Essential properties like icon paths are missing
- **Type mismatches** - Properties have wrong data types

### ⚠️ WARNING (Important)
- **Missing meta properties** - Components lack required metadata like names
- **Missing content** - Labels without text, missing child positioning
- **Accessibility concerns** - Interactive elements without proper labeling

### ℹ️ INFO (Informational)
- **Performance considerations** - Components that may impact performance
- **Best practice suggestions** - Recommendations for better structure
- **Layout recommendations** - Flex container usage patterns

### 💄 STYLE (Cosmetic)
- **Generic naming** - Components with non-descriptive names
- **Unnecessary containers** - Single-child flex containers
- **Layout inefficiencies** - Missing explicit direction properties

## Real-World Example Results

### Full Project Analysis
```bash
uv run python ignition-perspective-linter.py --target /path/to/whk-distillery01-ignition-global
```

**Results:**
- 📁 Files processed: 226
- 🧩 Components analyzed: 2,660
- ✅ Valid components: 2,533 (95.2%)
- ❌ Invalid components: 127
- 🔧 Component types: 36

**Issue Breakdown:**
- ❌ ERROR: 147 critical schema violations
- ⚠️ WARNING: 94 important issues  
- ℹ️ INFO: 497 informational items
- 💄 STYLE: 485 style suggestions

### Component-Specific Analysis
```bash
uv run python ignition-perspective-linter.py --target /path/to/project --component-type ia.display.label
```

**Results for Labels:**
- 🧩 Components analyzed: 829 labels
- ✅ Valid: 804 (97.0%)
- ❌ Invalid: 25
- Common issues: fontSize as number instead of string

## Common Issues Found

### 1. Schema Validation Errors
```json
// ❌ Wrong type - fontSize should be string
"textStyle": {
    "fontSize": 14  // Should be "14px"
}

// ❌ Wrong type - placeholder should be string  
"placeholder": {
    "text": "Select Option..."  // Should be "Select Option..."
}
```

### 2. Missing Required Properties
```json
// ❌ Icon missing required path
{
    "type": "ia.display.icon",
    "meta": {"name": "MyIcon"}
    // Missing: "props": {"path": "material/icon_name"}
}
```

### 3. Poor Accessibility
```json
// ⚠️ Button without descriptive text
{
    "type": "ia.input.button", 
    "meta": {"name": "Button"}  // Generic name
    // Missing: "props": {"text": "Submit Form"}
}
```

### 4. Style Issues
```json
// 💄 Single child in flex container
{
    "type": "ia.container.flex",
    "children": [/* only one child */]
    // Consider: Remove unnecessary flex wrapper
}
```

## Integration with Development Workflow

### CI/CD Pipeline Integration
```yaml
# .github/workflows/ignition-lint.yml
- name: Lint Ignition Components
  run: |
    uv run python ignition-perspective-linter.py \
      --target ./ignition-project \
      --output lint-report.txt
    if [ $? -ne 0 ]; then
      echo "Linting failed with critical errors"
      exit 1
    fi
```

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
uv run python tools/ignition-perspective-linter.py --target . > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Ignition component linting failed. Run linter for details."
    exit 1
fi
```

### IDE Integration
Many IDEs can be configured to run the linter and display results inline.

## Understanding the Output

### Summary Section
```
📊 LINTING REPORT
📁 Files processed: 226        # Total view.json files found
🧩 Components analyzed: 2660   # Total ia.* components
✅ Valid components: 2533      # Schema-compliant components  
❌ Invalid components: 127     # Components with errors
📈 Schema compliance: 95.2%   # Overall success rate
```

### Issue Details
```
📄 path/to/view.json
   ❌ SCHEMA_VALIDATION: fontSize should be string not number
      Component: ia.display.label at root.children[0]  
      Suggestion: Path: props.textStyle.fontSize
```

**Explanation:**
- **File Path:** Exact location of the problematic view
- **Issue Type:** Category and description of the problem
- **Component Location:** Path within the view structure
- **Suggestion:** Specific guidance for resolution

## Best Practices for Clean Code

### 1. Meaningful Naming
```json
// ✅ Good
{"meta": {"name": "UserStatusLabel"}}
{"meta": {"name": "SubmitOrderButton"}}

// ❌ Avoid  
{"meta": {"name": "Label"}}
{"meta": {"name": "Component"}}
```

### 2. Required Properties
```json
// ✅ Complete components
{
    "type": "ia.display.icon",
    "meta": {"name": "StatusIcon"}, 
    "props": {"path": "material/check_circle"}
}
```

### 3. Efficient Layouts
```json
// ✅ Multi-child flex containers
{
    "type": "ia.container.flex",
    "props": {"direction": "row"},
    "children": [/* multiple children */]
}
```

## Troubleshooting

### Common Schema Path Issues
- **Path:** `props.textStyle.fontSize` → Check font size is string like "14px"
- **Path:** `props.placeholder` → Ensure placeholder is simple string
- **Path:** `position.grow` → Verify grow values are numbers not strings

### Performance with Large Projects
- Use `--component-type` to focus on specific component types
- Run linting in CI/CD rather than locally for large codebases
- Save reports to files for analysis: `--output report.txt`

## Exit Codes

- **0:** Success (no critical errors)
- **1:** Failure (critical errors found or execution failed)

Use exit codes in automation to fail builds when critical issues are detected.

---

**The linter provides actionable insights to improve Ignition Perspective code quality, maintainability, and performance.**
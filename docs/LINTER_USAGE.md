# Ignition Lint Usage Guide

## Overview

`ignition-lint` is a comprehensive linting toolkit for Ignition SCADA projects. It validates Perspective `view.json` files against empirical schemas, checks expression bindings, validates Jython scripts, enforces naming conventions, and detects unused properties.

## Quick Start

```bash
# Lint any directory recursively (finds view.json + .py files automatically)
ignition-lint --target /path/to/any/folder

# Lint a standard Ignition project with all checks
ignition-lint --project /path/to/ignition/project --profile full

# Lint just Perspective views in a subdirectory
ignition-lint -t /path/to/views/MyScreen --checks perspective

# JSON output for AI agents / MCP
ignition-lint -t /path/to/folder --report-format json

# Filter by component type
ignition-lint --project /path/to/project --component ia.display.label

# Verbose output
ignition-lint --project /path/to/project --verbose
```

## Command Line Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--target` | `-t` | Path to **any** directory; recursively lints all `view.json` and `.py` files | `/path/to/any/folder` |
| `--project` | `-p` | Path to Ignition project directory (expects standard layout) | `/path/to/project` |
| `--checks` | | Comma-separated: `perspective`, `naming`, `scripts` | `--checks perspective,scripts` |
| `--profile` | | Preset: `default`, `full`, `perspective-only`, `scripts-only`, `naming-only` | `--profile full` |
| `--component` | `-c` | Filter Perspective linting to component type prefix | `-c ia.display.label` |
| `--schema-mode` | | Schema strictness: `strict`, `robust`, `permissive` | `--schema-mode robust` |
| `--verbose` | `-v` | Show detailed output with all issues | `--verbose` |
| `--report-format` | | Output format: `text` or `json` | `--report-format json` |
| `--fail-on` | | Severity threshold for non-zero exit | `--fail-on warning` |
| `--ignore-codes` | | Comma-separated rule codes to suppress | `--ignore-codes LONG_LINE` |
| `--ignore-file` | | Path to ignore file | `--ignore-file .lintignore` |

### `--target` vs `--project`

- **`--target`** accepts any directory and recursively discovers files. This is the preferred mode for AI agents, MCP integrations, and ad-hoc linting.
- **`--project`** expects the standard Ignition layout (`com.inductiveautomation.perspective/views/` and `ignition/script-python/`).

## Issue Severity Levels

### ❌ ERROR (Critical)
- **Schema validation failures** - Component structure doesn't match expected schema
- **Missing required properties** - Essential properties like icon paths are missing
- **Type mismatches** - Properties have wrong data types
- **Expression errors** - Malformed property references in expressions

### ⚠️ WARNING (Important)
- **Missing meta properties** - Components lack required metadata like names
- **Missing content** - Labels without text, missing child positioning
- **Accessibility concerns** - Interactive elements without proper labeling
- **Polling issues** - `now()` without explicit rate defaults to 1 000 ms
- **Fragile references** - `getSibling()`, `getParent()`, `getChild()` in scripts or expressions
- **Unused properties** - Custom properties defined but never referenced

### ℹ️ INFO (Informational)
- **Performance considerations** - Components that may impact performance
- **Best practice suggestions** - Recommendations for better structure
- **Layout recommendations** - Flex container usage patterns
- **Unknown functions** - Expression functions not in the known Ignition catalog
- **Low polling rates** - `now(N)` with N < 5 000 ms

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

## Suppressing Rules

When adopting the linter on an existing project, you can suppress noisy rules and address them incrementally. Three mechanisms are available:

| Mechanism | Scope | Example |
|-----------|-------|---------|
| `--ignore-codes` | Global | `--ignore-codes NAMING_PARAMETER,LONG_LINE` |
| `.ignition-lintignore` | Per-path | `views/_REFERENCE/**:NAMING_COMPONENT` |
| Inline comments | Per-line (scripts only) | `# ignition-lint: disable=LONG_LINE` |

See **[SUPPRESSION.md](SUPPRESSION.md)** for the complete reference including all inline directives, pattern syntax, and CI/CD integration examples.

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
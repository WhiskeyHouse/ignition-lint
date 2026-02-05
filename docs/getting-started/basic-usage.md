---
sidebar_position: 2
title: Basic Usage
---

# Basic Usage

## Lint Any Directory

Point the linter at **any** directory and it recursively finds and lints all `view.json` and `.py` files:

```bash
# Lint everything under a directory
ignition-lint --target /path/to/any/folder

# Lint just Perspective views in a subfolder
ignition-lint -t /path/to/views/ScheduleManagement --checks perspective

# Lint only scripts, output as JSON (for AI agents / MCP)
ignition-lint -t /path/to/scripts --checks scripts --report-format json
```

This is the recommended mode for AI agents, MCP integrations, and ad-hoc subdirectory linting.

## Lint a Full Ignition Project

If your directory follows the standard Ignition layout, `--project` auto-discovers the conventional paths:

```bash
ignition-lint --project /path/to/ignition/project --profile full
```

This looks for `com.inductiveautomation.perspective/views/` and `ignition/script-python/` and runs Perspective schema validation, naming convention checks, and script analysis in one pass.

## Lint Specific Files

Target individual `view.json` files with glob patterns:

```bash
ignition-lint --files "**/view.json" --component-style PascalCase --parameter-style camelCase
```

## Naming Conventions Only

Skip schema and script analysis to focus on naming:

```bash
ignition-lint --project /path/to/project --naming-only
```

## Understanding the Output

### Severity Levels

| Level | Meaning |
|---|---|
| **ERROR** | Critical issues that will cause runtime failures |
| **WARNING** | Compatibility or best practice issues |
| **INFO** | Informational insights and suggestions |
| **STYLE** | Code style and documentation improvements |

### Example Output

```
📊 LINT RESULTS
============================================================
📁 Files processed: 226
🧩 Components analyzed: 2,660
✅ Valid components: 2,533 (95.2%)
❌ Invalid components: 127

📋 Issues by severity:
  ❌ Error: 147
  ⚠️ Warning: 94
  ℹ️ Info: 497
  💡 Style: 485

📄 views/MainScreen/view.json
   ❌ SCHEMA_VALIDATION: fontSize should be string not number
      Component: ia.display.label at root.children[0]
      Suggestion: Path: props.textStyle.fontSize
```

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success (no critical errors) |
| `1` | Failure (critical errors found or execution failed) |

## Suppressing Noisy Rules

During initial adoption, suppress rules you're not ready to address:

```bash
ignition-lint -p ./project --profile full \
  --ignore-codes NAMING_PARAMETER,MISSING_DOCSTRING,LONG_LINE
```

See the [Suppression Guide](../guides/suppression.md) for the full reference.

## Common Issues and Fixes

### Schema Validation Errors

```json
// fontSize should be a string like "14px", not a number
"textStyle": {
    "fontSize": 14    // ERROR
    "fontSize": "14px" // OK
}
```

### Jython Indentation

Inline scripts in `view.json` must be indented (they execute inside an implicit function body):

```python
# ERROR: no indentation
if value == -1:
    return False

# OK: properly indented
    if value == -1:
        return False
```

### Print Statements

Use function-call syntax for Python 3 compatibility:

```python
print 'hello'    # WARNING: statement syntax
print('hello')   # OK: function syntax
```

## Next Steps

- [CLI Reference](../guides/cli-reference.md) — All command-line options
- [Rule Codes](../guides/rule-codes.md) — Every rule code explained
- [GitHub Actions](../integration/github-actions.md) — CI/CD integration

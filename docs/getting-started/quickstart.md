---
sidebar_position: 0
title: Quick Start
---

# 5-Minute Quick Start

Get up and running with ignition-lint in minutes. This guide walks you through installation, your first lint run, and common integration patterns.

## Prerequisites

- Python 3.10 or higher
- An Ignition project with Perspective views or Python scripts

## Installation

```bash
pip install ignition-lint-toolkit
```

Verify the installation:

```bash
ignition-lint --version
```

## Your First Lint

### Scenario 1: Lint a directory

Point ignition-lint at any directory containing Perspective views or Python scripts:

```bash
ignition-lint --target /path/to/your/ignition/project
```

This recursively finds all `view.json` files and `.py` files in `script-python` directories.

**Example output:**
```
Linting Perspective views...
✓ Found 45 view.json files

ERROR: JYTHON_SYNTAX_ERROR in views/Dashboard/view.json:23
  Line 5: unexpected indent in onChange script

WARNING: EXPR_NOW_DEFAULT_POLLING in views/Overview/view.json:67
  now() defaults to 1000ms polling - specify interval: now(5000)

WARNING: NAMING_COMPONENT in views/Home/view.json:12
  Component 'Label' should use PascalCase (e.g., 'StatusLabel')

=== Summary ===
Total issues: 12
Errors: 1
Warnings: 8
Info: 3
```

### Scenario 2: Lint a full Ignition project

If your directory follows the standard Ignition export structure:

```bash
ignition-lint --project /path/to/ignition/project --profile full
```

This looks for:
- `com.inductiveautomation.perspective/views/**/view.json`
- `script-python/**/*.py`

## Common Workflows

### Run only specific checks

```bash
# Only Perspective view validation
ignition-lint -t ./views --checks perspective

# Only Python script linting
ignition-lint -t ./scripts --checks scripts

# Only naming conventions
ignition-lint -p ./project --naming-only
```

### Filter by component type

Useful for large projects - focus on one component type at a time:

```bash
# Only lint Label components
ignition-lint -t ./views --component ia.display.label

# Only lint Dropdown components
ignition-lint -t ./views --component ia.input.dropdown
```

### JSON output for CI/CD

Get structured output for programmatic consumption:

```bash
ignition-lint -t ./project --report-format json > lint-report.json
```

**Example JSON output:**
```json
{
  "summary": {
    "total_issues": 12,
    "errors": 1,
    "warnings": 8,
    "info": 3,
    "style": 0
  },
  "issues": [
    {
      "code": "JYTHON_SYNTAX_ERROR",
      "severity": "ERROR",
      "file": "views/Dashboard/view.json",
      "line": 23,
      "message": "Line 5: unexpected indent in onChange script",
      "component_path": "root/Container_0"
    }
  ]
}
```

### Suppress noisy rules during adoption

When introducing linting to an existing project, suppress rules you plan to fix later:

```bash
# Suppress specific rule codes globally
ignition-lint -t ./project --ignore-codes NAMING_PARAMETER,LONG_LINE

# Only fail on errors (ignore warnings/info)
ignition-lint -t ./project --fail-on error
```

## Integration Patterns

### GitHub Actions

Create `.github/workflows/ignition-lint.yml`:

```yaml
name: Ignition Lint
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: TheThoughtagen/ignition-lint@v1
        with:
          project_path: .
          lint_type: all
          fail_on: error
```

This runs on every push and PR, failing the build if errors are found.

[Full GitHub Actions guide →](../integration/github-actions)

### Pre-commit hook

Catch issues before they're committed:

```bash
# Install pre-commit framework
pip install pre-commit

# Add to .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/TheThoughtagen/ignition-lint
    rev: v1
    hooks:
      - id: ignition-perspective-lint
EOF

# Install hooks
pre-commit install
```

Now ignition-lint runs automatically on `git commit`.

[Pre-commit guide →](../integration/pre-commit)

### VS Code integration

Add JSON schema validation for `view.json` files in `.vscode/settings.json`:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["**/perspective/views/**/view.json"],
      "url": "./node_modules/ignition-lint-toolkit/schemas/core-ia-components-schema-robust.json"
    }
  ]
}
```

This provides real-time validation and autocomplete in VS Code.

## Understanding Rule Codes

ignition-lint groups rules into categories:

| Prefix | Category | Examples |
|--------|----------|----------|
| `NAMING_` | Naming conventions | `NAMING_COMPONENT`, `NAMING_PARAMETER` |
| `JYTHON_` | Inline Jython scripts | `JYTHON_SYNTAX_ERROR`, `JYTHON_PRINT_STATEMENT` |
| `EXPR_` | Expression bindings | `EXPR_NOW_DEFAULT_POLLING`, `EXPR_INVALID_PROPERTY_REF` |
| `SCHEMA_` | JSON schema violations | `SCHEMA_VALIDATION_ERROR`, `SCHEMA_UNKNOWN_PROPERTY` |
| `MISSING_` | Documentation gaps | `MISSING_DOCSTRING` |
| `UNUSED_` | Dead code | `UNUSED_CUSTOM_PROPERTY`, `UNUSED_PARAM_PROPERTY` |

[Full rule code reference →](../guides/rule-codes)

## Suppression Strategies

Three ways to suppress rules:

### 1. Global suppression (CLI flag)
```bash
ignition-lint -t ./project --ignore-codes NAMING_PARAMETER,LONG_LINE
```

### 2. Per-project (`.ignition-lintignore`)
```
# .ignition-lintignore
# Ignore legacy views
legacy-views/**/*.json: *

# Ignore parameter naming in specific directory
dashboard/**/*.json: NAMING_PARAMETER

# Ignore all naming issues in generated files
generated/**/*.py: NAMING_*
```

### 3. Inline (Python scripts only)
```python
# ignition-lint: disable=MISSING_DOCSTRING
def quick_helper():
    pass

# ignition-lint: disable-next=LONG_LINE
some_variable = system.tag.readBlocking(['[default]Very/Long/Tag/Path/Here/With/Many/Levels'])[0].value
```

[Suppression guide →](../guides/suppression)

## Troubleshooting

### "No view.json files found"

**Problem:** The linter didn't find any files to lint.

**Solution:**
- Check your path: `ls -la /path/to/project/**/*view.json`
- Try `--target` instead of `--project` for non-standard layouts
- Verify you're pointing at the Ignition project root (contains `com.inductiveautomation.perspective/`)

### "Schema validation errors on custom components"

**Problem:** The linter flags valid custom components as errors.

**Solution:**
- Use `--schema-mode permissive` to allow any component type
- Or `--schema-mode robust` (default) for production-tested components only
- Add your custom component schemas to the schema directory

### "Too many NAMING_PARAMETER violations"

**Problem:** Existing project has thousands of parameter naming violations.

**Solution:**
```bash
# Suppress parameter naming during migration
ignition-lint -t ./project --ignore-codes NAMING_PARAMETER

# Or use .ignition-lintignore for specific paths
echo "legacy/**/*.json: NAMING_PARAMETER" >> .ignition-lintignore
```

### "False positive on tag paths with spaces"

**Problem:** `EXPR_INVALID_PROPERTY_REF` fires on valid tag paths like `[default]My Tag`.

**Solution:** This should be automatically excluded. If you're seeing this, please [report a bug](https://github.com/TheThoughtagen/ignition-lint/issues) with an example.

## Next Steps

- **[CLI Reference](../guides/cli-reference)** — Full command-line documentation
- **[Rule Codes](../guides/rule-codes)** — Complete list of lint rules
- **[GitHub Actions](../integration/github-actions)** — CI/CD integration
- **[MCP Server](../guides/mcp-server)** — AI agent integration

## Real-World Examples

### Manufacturing dashboard project
```bash
# Pre-deployment check - only fail on errors
ignition-lint -p ./manufacturing-hmi --fail-on error

# Output: 0 errors, 12 warnings (performance suggestions)
# Result: ✓ Safe to deploy
```

### Legacy project modernization
```bash
# Phase 1: Identify critical issues
ignition-lint -t ./legacy --ignore-codes NAMING_*,MISSING_DOCSTRING > phase1.txt

# Phase 2: Fix errors, track progress
ignition-lint -t ./legacy --fail-on error  # Initially fails
# ... fix syntax errors ...
ignition-lint -t ./legacy --fail-on error  # Now passes!

# Phase 3: Enable naming checks view-by-view
echo "legacy/old-views/**/*.json: NAMING_*" >> .ignition-lintignore
ignition-lint -t ./legacy --fail-on warning
```

### Multi-site consistency check
```bash
# Lint all sites with same rules
for site in site1 site2 site3; do
  echo "=== Linting $site ==="
  ignition-lint -p ./sites/$site --report-format json > reports/$site.json
done

# Compare reports
python scripts/compare-reports.py reports/*.json
```

---

**Need help?** [Open an issue](https://github.com/TheThoughtagen/ignition-lint/issues) or check the [full documentation](/).

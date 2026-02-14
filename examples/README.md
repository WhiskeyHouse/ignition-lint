# Ignition Lint Examples

This directory contains example Ignition projects demonstrating both **good practices** and **common issues** that ignition-lint catches.

## Directory Structure

```
examples/
├── good-practices/          # Clean project following best practices
│   ├── views/               # Well-structured Perspective views
│   └── scripts/             # Properly documented Python scripts
├── common-issues/           # Project with typical linting violations
│   ├── views/               # Views with naming, schema, and expression issues
│   └── scripts/             # Scripts with syntax errors and code smells
└── migration-example/       # Before/after example of adopting ignition-lint
    ├── before/              # Legacy project with many violations
    └── after/               # Same project after fixes + suppressions
```

> **Note:** The `common-issues/` directory is excluded from ruff checks (see `pyproject.toml`) since it intentionally contains broken code for demonstration purposes.

## Quick Start

### Lint the good practices example
```bash
cd examples/good-practices
ignition-lint --target .
```

Expected output: ✅ No issues found (or very few INFO-level suggestions)

### Lint the common issues example
```bash
cd examples/common-issues
ignition-lint --target .
```

Expected output: Multiple ERRORs, WARNINGs, and INFO messages demonstrating what ignition-lint catches.

### Compare before/after migration
```bash
# Before: Many violations
cd examples/migration-example/before
ignition-lint --target . | tee before-results.txt

# After: Clean (with strategic suppressions)
cd ../after
ignition-lint --target . | tee after-results.txt

# Compare
diff before-results.txt after-results.txt
```

## Example Scenarios

### 1. Good Practices (`good-practices/`)

Demonstrates:
- ✅ Proper component naming (PascalCase)
- ✅ Consistent parameter naming (camelCase)
- ✅ Documented scripts with docstrings
- ✅ Efficient `now()` polling intervals
- ✅ No unused custom properties
- ✅ Proper expression bindings
- ✅ Clean Jython scripts with error handling

### 2. Common Issues (`common-issues/`)

Demonstrates typical problems ignition-lint catches:
- ❌ Generic component names (`Label`, `Button`)
- ❌ Jython syntax errors in onChange scripts
- ❌ `now()` with default 1000ms polling
- ❌ Hardcoded URLs in scripts
- ❌ Print statements instead of logger
- ❌ Unused custom properties
- ❌ Fragile component traversal (`getSibling()`)
- ❌ Missing docstrings

### 3. Migration Example (`migration-example/`)

Shows realistic migration workflow:

**Before:**
- 50+ naming violations
- 10+ syntax errors
- 5+ performance issues

**After:**
- Strategic use of `.ignition-lintignore` for legacy views
- Fixed critical ERRORs
- Suppressed non-critical WARNINGs for gradual adoption
- Added inline suppressions where appropriate

## Example Workflows

### GitHub Actions Integration

Each example directory has a `.github/workflows/` showing different configurations:

#### Good Practices
```yaml
# Strict mode - no violations allowed
- uses: TheThoughtagen/ignition-lint@v1
  with:
    project_path: .
    fail_on: style  # Fail on any issue
```

#### Common Issues
```yaml
# Report mode - show issues but don't fail build
- uses: TheThoughtagen/ignition-lint@v1
  with:
    project_path: .
    fail_on: error  # Only fail on critical errors
    ignore_codes: "NAMING_COMPONENT,NAMING_PARAMETER"
```

#### Migration
```yaml
# Gradual adoption - suppress legacy issues
- uses: TheThoughtagen/ignition-lint@v1
  with:
    project_path: .
    fail_on: error
    # Uses .ignition-lintignore for fine-grained control
```

## Running Examples Locally

### Setup

```bash
# From repository root
cd examples
```

### Test All Examples

```bash
#!/bin/bash
# test-all-examples.sh

echo "=== Testing Good Practices ==="
ignition-lint -t good-practices/

echo -e "\n=== Testing Common Issues ==="
ignition-lint -t common-issues/

echo -e "\n=== Testing Migration (Before) ==="
ignition-lint -t migration-example/before/

echo -e "\n=== Testing Migration (After) ==="
ignition-lint -t migration-example/after/
```

Make executable and run:
```bash
chmod +x test-all-examples.sh
./test-all-examples.sh
```

## Learning from Examples

### Study the view.json files

Compare `good-practices/views/Dashboard.view.json` with `common-issues/views/Dashboard.view.json`:

**Good:**
```json
{
  "custom": {
    "refreshInterval": { ... }  // Used in binding
  },
  "props": {
    "StatusLabel": {  // PascalCase component name
      "type": "ia.display.label",
      ...
    }
  }
}
```

**Bad:**
```json
{
  "custom": {
    "unusedProperty": { ... }  // Never referenced
  },
  "props": {
    "Label": {  // Generic name
      "type": "ia.display.label",
      ...
    }
  }
}
```

### Study the Python scripts

Compare `good-practices/scripts/data_processing.py` with `common-issues/scripts/data_processing.py`:

**Good:**
```python
"""Data processing utilities for manufacturing metrics."""

import system.tag

def read_production_count(line_number):
    """
    Read current production count for a line.

    Args:
        line_number: Production line number (1-5)

    Returns:
        int: Current count or -1 on error
    """
    try:
        tag_path = f"[default]Line{line_number}/ProductionCount"
        result = system.tag.readBlocking([tag_path])
        return result[0].value if result[0].quality.isGood() else -1
    except Exception as e:
        logger = system.util.getLogger("DataProcessing")
        logger.error(f"Failed to read production count: {e}")
        return -1
```

**Bad:**
```python
import system.tag

def read_count(line):  # Missing docstring
    tag = "[default]Line" + str(line) + "/ProductionCount"  # Use f-string
    result = system.tag.readBlocking([tag])
    print result[0].value  # Python 2 syntax error!
```

## Contributing Examples

Have a great example demonstrating a specific ignition-lint feature or common pattern?

1. Create a directory under `examples/`
2. Add a README explaining what it demonstrates
3. Include sample view.json and/or .py files
4. Submit a PR!

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Next Steps

- **[Quick Start Guide](../docs/getting-started/quickstart.md)** — Get started with ignition-lint
- **[Rule Codes Reference](../docs/guides/rule-codes.md)** — Understand what each rule checks
- **[Suppression Guide](../docs/guides/suppression.md)** — Learn how to control which rules fire

---

**Questions?** [Open an issue](https://github.com/TheThoughtagen/ignition-lint/issues)

# Ignition Lint GitHub Action

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-ignition--lint-blue?logo=github)](https://github.com/marketplace/actions/ignition-lint)
[![CI](https://github.com/TheThoughtagen/ignition-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/TheThoughtagen/ignition-lint/actions/workflows/ci.yml)

**Automatically lint your Ignition SCADA projects in CI/CD** - catch errors, enforce naming conventions, and maintain code quality before deployment.

## Quick Start

Add to your workflow (`.github/workflows/ignition-lint.yml`):

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
          files: "**/view.json"
          component_style: "PascalCase"
          parameter_style: "camelCase"
```

This runs on every push and PR, failing if naming violations are found.

## What It Checks

| Category | Examples |
|----------|----------|
| **Perspective schema** | Component structure, binding types, transform validity |
| **Expressions** | `now()` polling intervals, malformed property refs, component traversal |
| **Naming conventions** | Component, parameter, and custom property naming (PascalCase, camelCase, snake_case, or custom regex) |
| **Jython scripts** | Syntax errors, print statements, hardcoded URLs, missing error handling |
| **Python scripts** | Syntax, docstrings, deprecated APIs, line length |
| **Unused properties** | Unreferenced custom and params properties |

## Inputs

### Basic Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `files` | No | `**/view.json` | Comma-separated file globs to lint |
| `project_path` | No | — | Path to Ignition project (alternative to `files`) |
| `version` | No | latest | Version of ignition-lint-toolkit to install |

### Linting Configuration

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `lint_type` | No | `perspective` | Type of linting: `perspective`, `scripts`, or `all` |
| `naming_only` | No | `true` | Only run naming convention checks |
| `checks` | No | — | Comma-separated: `perspective`, `naming`, `scripts` |

### Naming Conventions

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `component_style` | No | `PascalCase` | Naming convention for components |
| `parameter_style` | No | `camelCase` | Naming convention for parameters |
| `component_style_rgx` | No | — | Custom regex for component names |
| `parameter_style_rgx` | No | — | Custom regex for parameter names |
| `allow_acronyms` | No | `false` | Allow acronyms in names (e.g., `HTTPClient`) |

### Advanced Options

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `ignore_codes` | No | — | Comma-separated rule codes to suppress globally |
| `schema_mode` | No | `robust` | Schema strictness: `strict`, `robust`, or `permissive` |
| `fail_on` | No | `error` | Minimum severity causing failure: `error`, `warning`, `info`, `style` |
| `component` | No | — | Filter to specific component type (e.g., `ia.display.label`) |

## Outputs

| Output | Description |
|--------|-------------|
| `result` | `success` or `failure` |

## Examples

### Full Project Lint

Lint everything (Perspective + scripts) and fail on errors:

```yaml
- uses: TheThoughtagen/ignition-lint@v1
  with:
    project_path: .
    lint_type: all
    naming_only: "false"
    fail_on: error
```

### Naming Only with Acronyms

Allow acronyms like `HTTPClient` or `APIKey`:

```yaml
- uses: TheThoughtagen/ignition-lint@v1
  with:
    files: "**/view.json"
    component_style: "PascalCase"
    parameter_style: "camelCase"
    allow_acronyms: "true"
```

### Custom Regex Patterns

Enforce your own naming rules:

```yaml
- uses: TheThoughtagen/ignition-lint@v1
  with:
    files: "**/view.json"
    component_style_rgx: "^[A-Z][a-zA-Z0-9]*_v[0-9]+$"  # e.g., Dashboard_v2
    parameter_style_rgx: "^[a-z][a-zA-Z0-9]*$"          # strict camelCase
```

### Gradual Adoption

Suppress rules you plan to fix later:

```yaml
- uses: TheThoughtagen/ignition-lint@v1
  with:
    project_path: .
    lint_type: all
    ignore_codes: "NAMING_PARAMETER,MISSING_DOCSTRING,LONG_LINE"
    fail_on: error  # Only block on actual errors
```

### Lint Specific Component Types

Focus on one component type at a time:

```yaml
strategy:
  matrix:
    component: [ia.display.label, ia.input.dropdown, ia.container.flex]
steps:
  - uses: TheThoughtagen/ignition-lint@v1
    with:
      project_path: .
      component: ${{ matrix.component }}
```

### Pin to Specific Version

For reproducible builds:

```yaml
- uses: TheThoughtagen/ignition-lint@v1
  with:
    version: "0.2.0"  # Pin to specific release
    project_path: .
```

### Matrix Testing (Multiple Projects)

Lint multiple Ignition projects in one workflow:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project: [manufacturing-hmi, warehouse-hmi, utilities-hmi]
    steps:
      - uses: actions/checkout@v4
      - uses: TheThoughtagen/ignition-lint@v1
        with:
          project_path: ./projects/${{ matrix.project }}
          lint_type: all
```

## How It Works

The action:

1. **Sets up Python 3.10**
2. **Installs ignition-lint-toolkit** from PyPI (`pip install ignition-lint-toolkit`)
3. **Runs the linter** with your configured options
4. **Exits with code 0** (success) or **1** (failure) based on findings

All inputs are passed as environment variables (`INPUT_*`) to the `ignition-lint-action` command.

## Versioning

| Tag | Description |
|-----|-------------|
| `@v1` | Latest stable v1.x release (recommended) |
| `@v1.2.3` | Pin to specific release |
| `@main` | Latest development (not recommended for production) |

**Recommendation:** Use `@v1` for automatic patch updates while staying on the stable v1.x line.

## Suppression Strategies

Three complementary mechanisms:

### 1. Global suppression (this action)

```yaml
with:
  ignore_codes: "NAMING_PARAMETER,LONG_LINE"
```

### 2. Per-project (`.ignition-lintignore`)

```
# .ignition-lintignore in your repo root
legacy-views/**/*.json: *
dashboard/**/*.json: NAMING_PARAMETER
generated/**/*.py: NAMING_*
```

### 3. Inline (Python scripts only)

```python
# ignition-lint: disable=MISSING_DOCSTRING
def helper():
    pass
```

[Full suppression guide →](https://TheThoughtagen.github.io/ignition-lint/guides/suppression)

## Troubleshooting

### Action fails with "No files found"

**Problem:** The linter didn't find any files to lint.

**Solution:**
- Check your `files` glob pattern
- Use `project_path` for standard Ignition layouts
- Verify your Ignition project structure

### Too many violations blocking PRs

**Problem:** Existing project has thousands of issues.

**Solution:**
```yaml
with:
  ignore_codes: "NAMING_PARAMETER,NAMING_COMPONENT"
  fail_on: error  # Only block on critical errors
```

Then gradually tighten rules as you fix issues.

### Custom components flagged as invalid

**Problem:** The linter doesn't recognize your custom components.

**Solution:**
```yaml
with:
  schema_mode: permissive  # Allow any component type
```

## Migration from ia-eknorr/ignition-lint

This action extends [ia-eknorr/ignition-lint](https://github.com/ia-eknorr/ignition-lint) with additional features:

| Feature | ia-eknorr | TheThoughtagen |
|---------|-----------|----------------|
| Naming validation | ✓ | ✓ |
| Script linting | — | ✓ |
| Schema validation | — | ✓ |
| Expression checking | — | ✓ |
| Suppression | — | ✓ |
| CLI tool | — | ✓ |

**Migration:**

```diff
- uses: ia-eknorr/ignition-lint@v1
+ uses: TheThoughtagen/ignition-lint@v1
  with:
    files: "**/view.json"
    component_style: "PascalCase"
    parameter_style: "camelCase"
```

No other changes needed!

## Related Resources

- **[Full Documentation](https://TheThoughtagen.github.io/ignition-lint/)** — Complete guide
- **[PyPI Package](https://pypi.org/project/ignition-lint-toolkit/)** — CLI tool
- **[Rule Codes](https://TheThoughtagen.github.io/ignition-lint/guides/rule-codes)** — What gets flagged
- **[CLI Reference](https://TheThoughtagen.github.io/ignition-lint/guides/cli-reference)** — Command-line options
- **[Pre-commit Hook](https://TheThoughtagen.github.io/ignition-lint/integration/pre-commit)** — Local integration

## Contributing

Contributions welcome! See [CONTRIBUTING.md](https://github.com/TheThoughtagen/ignition-lint/blob/main/CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](https://github.com/TheThoughtagen/ignition-lint/blob/main/LICENSE) © 2025 Patrick Mannion

---

**Need help?** [Open an issue](https://github.com/TheThoughtagen/ignition-lint/issues) or check the [documentation](https://TheThoughtagen.github.io/ignition-lint/).

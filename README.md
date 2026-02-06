# ignition-lint

[![PyPI](https://img.shields.io/pypi/v/ignition-lint-toolkit)](https://pypi.org/project/ignition-lint-toolkit/)
[![Python](https://img.shields.io/pypi/pyversions/ignition-lint-toolkit)](https://pypi.org/project/ignition-lint-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/WhiskeyHouse/ignition-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/WhiskeyHouse/ignition-lint/actions/workflows/ci.yml)

A comprehensive linting toolkit for [Ignition SCADA](https://inductiveautomation.com/) projects. Validates Perspective views, Jython scripts, naming conventions, expressions, and more.

> This project extends the foundational work by [Eric Knorr](https://github.com/ia-eknorr) in [ia-eknorr/ignition-lint](https://github.com/ia-eknorr/ignition-lint), which pioneered naming convention validation for Ignition view.json files. See [credits](https://WhiskeyHouse.github.io/ignition-lint/credits) for the full story.

## Installation

```bash
pip install ignition-lint-toolkit
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install ignition-lint-toolkit
```

Verify the install:

```bash
ignition-lint --help
```

### Optional: MCP server support

```bash
pip install "ignition-lint-toolkit[mcp]"
```

## Quick start

### Lint any directory

Point the linter at any directory and it recursively finds `view.json` and `.py` files:

```bash
ignition-lint --target /path/to/your/project
```

### Lint a full Ignition project

If your directory follows the standard Ignition layout:

```bash
ignition-lint --project /path/to/ignition/project --profile full
```

### Pick specific checks

```bash
# Only Perspective views
ignition-lint -t /path/to/views --checks perspective

# Only scripts, JSON output for programmatic use
ignition-lint -t /path/to/scripts --checks scripts --report-format json

# Naming conventions only
ignition-lint --project /path/to/project --naming-only
```

### Suppress noisy rules during adoption

```bash
ignition-lint -t ./project --ignore-codes NAMING_PARAMETER,MISSING_DOCSTRING,LONG_LINE
```

## What it checks

| Category | Examples |
|---|---|
| **Perspective schema** | Component structure, binding types, transform validity, missing props |
| **Expressions** | `now()` polling intervals, unknown functions, malformed property refs, fragile component traversal |
| **Naming conventions** | Component, parameter, and custom property naming (PascalCase, camelCase, snake_case, or custom regex) |
| **Jython inline scripts** | Syntax errors, indentation, `print` statements, hardcoded URLs, missing error handling |
| **Standalone scripts** | Python syntax, docstrings, deprecated APIs, `system` overrides, line length |
| **Unused properties** | Unreferenced `custom` and `params` properties per view |

## Severity levels

| Level | Meaning |
|---|---|
| **ERROR** | Critical issues that cause runtime failures |
| **WARNING** | Compatibility or best practice issues |
| **INFO** | Informational insights and suggestions |
| **STYLE** | Code style and documentation improvements |

## Lint suppression

Three mechanisms let you control which rules fire and where:

1. **`--ignore-codes` flag** -- suppress rules globally for an entire run
2. **`.ignition-lintignore` file** -- gitignore-style patterns with optional rule scoping per path
3. **Inline comments** -- `# ignition-lint: disable=CODE` directives in Python scripts

See the [suppression guide](https://WhiskeyHouse.github.io/ignition-lint/guides/suppression) for the full reference.

## Integrations

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
      - uses: whiskeyhouse/ignition-lint@v1
        with:
          files: "**/view.json"
          component_style: "PascalCase"
          parameter_style: "camelCase"
```

### Pre-commit hook

```yaml
repos:
  - repo: https://github.com/WhiskeyHouse/ignition-lint
    rev: v1
    hooks:
      - id: ignition-perspective-lint
```

### MCP server (AI agents)

```bash
ignition-lint-server
```

## Tooling overview

| Command | Purpose |
|---|---|
| `ignition-lint` | CLI entry point for project and file linting |
| `ignition-lint-server` | FastMCP server for AI agent integrations |
| `ignition-lint-action` | Wrapper used by the GitHub Action |

## Documentation

Full documentation at [WhiskeyHouse.github.io/ignition-lint](https://WhiskeyHouse.github.io/ignition-lint/):

- [Installation](https://WhiskeyHouse.github.io/ignition-lint/getting-started/installation)
- [Basic usage](https://WhiskeyHouse.github.io/ignition-lint/getting-started/basic-usage)
- [CLI reference](https://WhiskeyHouse.github.io/ignition-lint/guides/cli-reference)
- [Rule codes](https://WhiskeyHouse.github.io/ignition-lint/guides/rule-codes)
- [Suppression guide](https://WhiskeyHouse.github.io/ignition-lint/guides/suppression)
- [GitHub Actions](https://WhiskeyHouse.github.io/ignition-lint/integration/github-actions)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, project structure, and guidelines.

## License

[MIT](LICENSE) &copy; Whiskey House Labs

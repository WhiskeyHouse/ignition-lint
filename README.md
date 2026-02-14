# ignition-lint

[![PyPI](https://img.shields.io/pypi/v/ignition-lint-toolkit)](https://pypi.org/project/ignition-lint-toolkit/)
[![Downloads](https://img.shields.io/pypi/dm/ignition-lint-toolkit)](https://pypi.org/project/ignition-lint-toolkit/)
[![Python](https://img.shields.io/pypi/pyversions/ignition-lint-toolkit)](https://pypi.org/project/ignition-lint-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/TheThoughtagen/ignition-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/TheThoughtagen/ignition-lint/actions/workflows/ci.yml)
[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-ignition--lint-blue?logo=github)](https://github.com/marketplace/actions/ignition-lint)

**A comprehensive linting toolkit for [Ignition SCADA](https://inductiveautomation.com/) projects** that catches errors before runtime, enforces best practices, and maintains code quality across your industrial automation systems.

> This project extends the foundational work by [Eric Knorr](https://github.com/ia-eknorr) in [ia-eknorr/ignition-lint](https://github.com/ia-eknorr/ignition-lint), which pioneered naming convention validation for Ignition view.json files. See [credits](https://TheThoughtagen.github.io/ignition-lint/credits) for the full story.

## Why ignition-lint?

**Catch errors before they reach runtime**
- Detect Jython syntax errors in onChange scripts and bindings
- Find malformed expression bindings and property references
- Validate against production-tested JSON schemas

**Maintain consistent standards across teams**
- Enforce naming conventions for components, parameters, and properties
- Flag deprecated API usage (`print` statements, `.iteritems()`, `xrange()`)
- Identify code smells like hardcoded URLs and overridden `system` variables

**Improve performance and maintainability**
- Detect `now()` expressions with inefficient polling intervals
- Find unreferenced custom properties and parameters
- Warn about fragile component traversal (`getSibling()`, `getChild()`)

**Integrate everywhere**
- GitHub Actions for automated PR checks
- Pre-commit hooks for local validation
- CLI for CI/CD pipelines
- MCP server for AI-assisted development

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

### Install
```bash
pip install ignition-lint-toolkit
```

### Lint your first project
```bash
# Lint any directory - finds all view.json and .py files
ignition-lint --target /path/to/your/project

# Or lint a full Ignition project (standard layout)
ignition-lint --project /path/to/ignition/project --profile full
```

### See what it catches
```bash
# Example output:
ERROR: JYTHON_SYNTAX_ERROR in MyView/view.json:45
  Syntax error in onChange script: unexpected indent

WARNING: EXPR_NOW_DEFAULT_POLLING in Dashboard/view.json:12
  now() defaults to 1000ms polling - specify explicit interval: now(5000)

WARNING: NAMING_COMPONENT in Home/view.json:8
  Component 'Label' should use PascalCase: 'StatusLabel'

INFO: UNUSED_CUSTOM_PROPERTY in Settings/view.json:23
  Custom property 'debugMode' is defined but never referenced
```

### Common use cases

```bash
# Pre-deployment validation
ignition-lint --project ./production --fail-on error

# Focus on one component type
ignition-lint -t ./views --component ia.display.label

# JSON output for CI/CD pipelines
ignition-lint -t ./project --report-format json > lint-report.json

# Suppress rules during gradual adoption
ignition-lint -t ./legacy --ignore-codes NAMING_PARAMETER,MISSING_DOCSTRING
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

See the [suppression guide](https://TheThoughtagen.github.io/ignition-lint/guides/suppression) for the full reference.

## Integrations

### 🔄 GitHub Actions

Automatically lint PRs and commits. Add to `.github/workflows/ignition-lint.yml`:

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
          ignore_codes: "NAMING_PARAMETER"  # Suppress during migration
```

[Full Action documentation →](https://TheThoughtagen.github.io/ignition-lint/integration/github-actions)

### 🪝 Pre-commit hooks

Catch issues before they're committed:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/TheThoughtagen/ignition-lint
    rev: v1
    hooks:
      - id: ignition-perspective-lint
```

[Pre-commit guide →](https://TheThoughtagen.github.io/ignition-lint/integration/pre-commit)

### 🤖 MCP server (AI agents)

Enable AI assistants like Claude to lint your Ignition projects:

```bash
pip install "ignition-lint-toolkit[mcp]"
ignition-lint-server
```

[MCP integration guide →](https://TheThoughtagen.github.io/ignition-lint/guides/mcp-server)

### 🛠️ Editor integration

#### VS Code / ignition-nvim
Use with language servers for real-time feedback. See [Editor Integration Guide](#) for setup with:
- VS Code with JSON schema validation
- Neovim with ignition-nvim
- LSP-compatible editors

## Tooling overview

| Command | Purpose |
|---|---|
| `ignition-lint` | CLI entry point for project and file linting |
| `ignition-lint-server` | FastMCP server for AI agent integrations |
| `ignition-lint-action` | Wrapper used by the GitHub Action |

## Documentation

Full documentation at [TheThoughtagen.github.io/ignition-lint](https://TheThoughtagen.github.io/ignition-lint/):

- [Installation](https://TheThoughtagen.github.io/ignition-lint/getting-started/installation)
- [Basic usage](https://TheThoughtagen.github.io/ignition-lint/getting-started/basic-usage)
- [CLI reference](https://TheThoughtagen.github.io/ignition-lint/guides/cli-reference)
- [Rule codes](https://TheThoughtagen.github.io/ignition-lint/guides/rule-codes)
- [Suppression guide](https://TheThoughtagen.github.io/ignition-lint/guides/suppression)
- [GitHub Actions](https://TheThoughtagen.github.io/ignition-lint/integration/github-actions)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, project structure, and guidelines.

## License

[MIT](LICENSE) &copy; 2025 Patrick Mannion

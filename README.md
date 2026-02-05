# Ignition Lint

A comprehensive linting toolkit for Ignition® projects that combines naming convention validation, empirical schema checks, and CI/CD automation.

> **🙏 Acknowledgments**: The naming convention validation features in this project were inspired by the excellent work by [Eric Knorr](https://github.com/ia-eknorr) in the [ia-eknorr/ignition-lint](https://github.com/ia-eknorr/ignition-lint) repository. We extend that foundation with broader project linting and automation support.

## ✨ Features

- **🎯 Naming Validation** – Enforces component and parameter styles across `view.json` files
- **📋 Perspective Linting** – Schema-aware checks against Perspective views, bindings, and event scripts
- **🔢 Expression Validation** – Detects `now()` polling issues, unknown functions, and fragile component references in Ignition expressions
- **📜 Script Analysis** – Validates inline Jython (from `view.json`) and standalone Python scripts in `script-python` directories
- **🔍 Unused Property Detection** – Flags unreferenced `custom` and `params` properties per view
- **🔇 Lint Suppression** – Suppress rules via CLI flags, ignore files, or inline comments
- **⚡ FastMCP Server** – Provides AI agent integration for real-time validation workflows
- **🚀 GitHub Action** – Drop-in CI integration for automated linting on push or PR
- **🔧 CLI Tooling** – `--target` for any directory, `--project` for Ignition layouts, JSON output for agents
- **📊 Production Data** – Rules validated across 12,220+ real industrial components

## 🔄 Relationship to ia-eknorr/ignition-lint

| Feature | ia-eknorr/ignition-lint | whiskeyhouse/ignition-lint |
|---------|------------------------|---------------------------|
| **View.json naming validation** | ✅ Core feature | ✅ Enhanced implementation |
| **Component style checking** | ✅ PascalCase, camelCase, etc. | ✅ Same styles + custom regex |
| **Parameter style checking** | ✅ Multiple styles supported | ✅ Same + enhanced validation |
| **GitHub Actions integration** | ✅ Simple action | ✅ Enhanced action + examples |
| **CLI tool** | ❌ Action-only | ✅ Full CLI with local development |
| **Project-wide linting** | ❌ Files only | ✅ Entire Ignition projects |
| **Script validation** | ❌ View.json only | ✅ Python/Jython scripts |
| **Empirical validation** | ❌ Naming only | ✅ Production-validated rules |
| **MCP/AI integration** | ❌ Not available | ✅ FastMCP server for AI agents |
| **Installation method** | GitHub Action only | ✅ `pip` / `uv` + GitHub Action |

### When To Use Which

Use [ia-eknorr/ignition-lint](https://github.com/ia-eknorr/ignition-lint) when you only need the original naming checks and a lightweight GitHub Action.

Use **whiskeyhouse/ignition-lint** when you want local CLI tooling, broader schema validation, MCP integration, or multiple lint types in CI.

## 🚀 Quick Start

### Install

```bash
# Install from PyPI
pip install ignition-lint

# Or use uv for workspace management
uv sync
```

### CLI Usage

```bash
# Lint any directory recursively (finds view.json + .py files automatically)
ignition-lint --target /path/to/any/folder

# Lint a subdirectory for just Perspective views
ignition-lint -t /path/to/views/MyScreen --checks perspective

# Lint scripts only, JSON output for AI agent / MCP consumption
ignition-lint -t /path/to/scripts --checks scripts --report-format json

# Lint a standard Ignition project with all checks
ignition-lint --project /path/to/project --profile full

# Naming convention validation only
ignition-lint --project /path/to/project --naming-only

# Suppress specific rules globally
ignition-lint --project /path/to/project --profile full --ignore-codes NAMING_PARAMETER,LONG_LINE
```

### GitHub Actions

Add to `.github/workflows/ignition-lint.yml`:

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
          ignore_codes: ""  # optional: comma-separated rule codes to suppress
```

## 🛠️ Tooling Overview

- `ignition-lint` – CLI entry point for project and file linting
- `ignition-lint-server` – FastMCP server for agent integrations
- `ignition-lint-action` – Wrapper used by the GitHub Action

## 📁 Project Layout

```
.
├── src/ignition_lint/           # Core package modules (CLI, server, checkers)
├── docs/                        # Detailed strategy and integration guides
├── examples/                    # Example scripts and views for demo scenarios
├── schemas/                     # Component schemas and supporting data
├── scripts/                     # Analysis tooling and supporting utilities
├── tests/                       # Automated tests
├── ignition-lint                # Convenience entry point for the CLI
├── action.yml                   # GitHub Action definition
├── pyproject.toml               # Project metadata and build configuration
└── uv.lock                      # Resolved dependency versions (uv)
```

## 📚 Documentation Highlights

- `docs/SUPPRESSION.md` – Suppressing rules: CLI flags, ignore files, inline comments
- `docs/IGNITION-LINTER-INTEGRATION.md` – Integrating the linter into Ignition projects
- `docs/LINTER-INTEGRATION-STRATEGY.md` – Recommended adoption patterns
- `docs/VALIDATION-LINTING-STRATEGY.md` – Deep dive into validation methodology
- `examples/` – Ready-to-run scenarios for demonstrating linting outcomes

## 🔇 Lint Suppression

Three mechanisms let you control which rules fire and where:

1. **`--ignore-codes` flag** – Suppress rules globally across the entire run
2. **`.ignition-lintignore` file** – Gitignore-style patterns with optional rule scoping per path
3. **Inline comments** – `# ignition-lint: disable=CODE` directives in Python scripts

```bash
# Suppress rules from the command line
ignition-lint -p ./project --profile full --ignore-codes NAMING_PARAMETER,NAMING_COMPONENT
```

```gitignore
# .ignition-lintignore — place in your --project root
scripts/generated/**
com.inductiveautomation.perspective/views/_REFERENCE/**:NAMING_COMPONENT,GENERIC_COMPONENT_NAME
```

```python
# ignition-lint: disable-file=MISSING_DOCSTRING
def legacy_helper():
    pass
```

See **[docs/SUPPRESSION.md](docs/SUPPRESSION.md)** for the full guide including all directive types, pattern syntax, rule code reference, and CI/CD examples.

## 🤖 FastMCP Integration

Run the FastMCP server to expose linting capabilities to AI agents:

```bash
ignition-lint-server --project /path/to/project
```

Connect FastMCP-compatible clients to the server for conversational linting, contextual file inspection, and auto-fix suggestions.

## 🧪 Testing

Use `uv` or `pytest` to run the test suite:

```bash
uv run pytest
# or
pytest
```

## 📄 License

MIT License. See `LICENSE` for details.

# Ignition Lint

A comprehensive linting toolkit for Ignition® projects that combines naming convention validation, empirical schema checks, and CI/CD automation.

> **🙏 Acknowledgments**: The naming convention validation features in this project were inspired by the excellent work by [Eric Knorr](https://github.com/ia-eknorr) in the [ia-eknorr/ignition-lint](https://github.com/ia-eknorr/ignition-lint) repository. We extend that foundation with broader project linting and automation support.

## ✨ Features

- **🎯 Naming Validation** – Enforces component and parameter styles across `view.json` files
- **📋 Perspective Linting** – Runs schema-aware checks against Perspective views and resources
- **⚡ FastMCP Server** – Provides AI agent integration for real-time validation workflows
- **🚀 GitHub Action** – Drop-in CI integration for automated linting on push or PR
- **🔧 CLI Tooling** – Local developer workflow with project-wide linting modes
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
# Lint view.json files for naming conventions
ignition-lint --files "**/view.json" --component-style PascalCase --parameter-style camelCase

# Lint an entire Ignition project with all checks
ignition-lint --project /path/to/project --type all

# Naming convention validation only
ignition-lint --project /path/to/project --naming-only
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

- `docs/IGNITION-LINTER-INTEGRATION.md` – Integrating the linter into Ignition projects
- `docs/LINTER-INTEGRATION-STRATEGY.md` – Recommended adoption patterns
- `docs/VALIDATION-LINTING-STRATEGY.md` – Deep dive into validation methodology
- `examples/` – Ready-to-run scenarios for demonstrating linting outcomes

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

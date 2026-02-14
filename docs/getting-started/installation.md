---
sidebar_position: 1
title: Installation
---

# Installation

## Prerequisites

- **Python 3.10+**
- **pip** or **uv** package manager
- Access to Ignition Perspective project files

## Install from PyPI

```bash
pip install ignition-lint-toolkit
```

## Install with uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager ideal for workspace management.

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and set up the project
git clone https://github.com/TheThoughtagen/ignition-lint.git
cd ignition-lint

# Install dependencies
uv sync
```

## Install from source

```bash
git clone https://github.com/TheThoughtagen/ignition-lint.git
cd ignition-lint

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

## Verify installation

```bash
ignition-lint --help
```

You should see the CLI help output with available options and commands.

## IDE Integration

### VS Code

If you cloned the repository, add the Ignition component schema to your `settings.json` for inline validation:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["**/perspective/views/**/view.json"],
      "url": "./schemas/core-ia-components-schema-robust.json"
    }
  ]
}
```

For pip-installed users, find the schema path with:

```bash
python -c "from ignition_lint.schemas import schema_path_for; print(schema_path_for('robust'))"
```

Then use the printed absolute path as the `"url"` value.

## Next Steps

- [Basic Usage](./basic-usage.md) — Lint your first project

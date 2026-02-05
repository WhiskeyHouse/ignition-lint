---
sidebar_position: 4
title: MCP Server
---

# FastMCP Server

ignition-lint includes a [FastMCP](https://github.com/jlowin/fastmcp) server that exposes linting capabilities to AI agents and MCP-compatible clients.

## Starting the Server

```bash
ignition-lint-server --project /path/to/project
```

The server starts and registers tools and resources that MCP clients can discover and invoke.

## Available Tools

### `check_linter_status`

Verify that the linting schema is available and report the current schema mode.

**Returns:** JSON with `available`, `schema_mode`, and `schema_path` fields.

### `lint_perspective_components`

Lint Perspective `view.json` files in an Ignition project.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `project_path` | string | Yes | Path to the Ignition project root |
| `component_type` | string | No | Filter to a specific component type |
| `verbose` | boolean | No | Show detailed output |
| `ignore_codes` | string | No | Comma-separated rule codes to suppress |

### `lint_jython_scripts`

Lint Python/Jython scripts in the `script-python` directory.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `project_path` | string | Yes | Path to the Ignition project root |
| `verbose` | boolean | No | Show detailed output |
| `ignore_codes` | string | No | Comma-separated rule codes to suppress |

### `lint_ignition_project`

Run comprehensive linting across the entire project (Perspective, naming, scripts).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `project_path` | string | Yes | Path to the Ignition project root |
| `lint_type` | string | No | `all`, `perspective`, `naming`, or `scripts` (default: `all`) |
| `component_type` | string | No | Filter to a specific component type |
| `verbose` | boolean | No | Show detailed output |
| `ignore_codes` | string | No | Comma-separated rule codes to suppress |

## Available Resources

### `ignition://linter/status`

Returns a JSON object with the current linter status, schema availability, and schema path.

### `ignition://linter/help`

Returns a usage guide listing all available tools and their parameters.

## Using `--target` with AI Agents

For AI agent and MCP workflows, the CLI's `--target` flag is the preferred interface. It accepts any directory and recursively discovers `view.json` and `.py` files without requiring a standard Ignition project layout:

```bash
# Lint any directory, JSON output for programmatic consumption
ignition-lint --target /path/to/any/folder --report-format json

# Lint only Perspective views in a subdirectory
ignition-lint -t /path/to/views/MyScreen --checks perspective --report-format json

# Lint only scripts
ignition-lint -t /path/to/scripts --checks scripts --report-format json
```

The JSON output includes structured issue data with file paths, severity, rule codes, component paths, and suggestions — ideal for agent-driven triage and auto-fix workflows.

## Example: Calling from an MCP Client

```python
# Using an MCP-compatible client
result = client.call_tool(
    "lint_ignition_project",
    project_path="/path/to/project",
    lint_type="all",
    ignore_codes="NAMING_PARAMETER,LONG_LINE",
)
print(result)
```

## Suppression Support

All tool functions accept an optional `ignore_codes` parameter (comma-separated string). The `.ignition-lintignore` file in the project root is also read automatically. See the [Suppression Guide](./suppression.md) for details.

## New Rule Categories

The linter now includes additional checks surfaced through the MCP server:

- **Expression rules** (`EXPR_*`) — `now()` polling, unknown functions, malformed property refs, fragile component traversal
- **Unused property rules** (`UNUSED_CUSTOM_PROPERTY`, `UNUSED_PARAM_PROPERTY`) — dead custom/param properties per view
- **Bad component ref** (`JYTHON_BAD_COMPONENT_REF`) — fragile `getSibling`/`getParent`/`getChild`/`getComponent` usage in scripts

See the [Rule Codes](./rule-codes.md) reference for the complete list.

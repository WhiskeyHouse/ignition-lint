---
sidebar_position: 1
title: CLI Reference
---

# CLI Reference

## Synopsis

```bash
ignition-lint [OPTIONS]
```

## Options

| Option | Short | Description | Default |
|---|---|---|---|
| `--project` | `-p` | Path to Ignition project directory (expects standard Ignition layout) | — |
| `--target` | `-t` | Path to **any** directory — recursively lints all `view.json` and `.py` files found | — |
| `--files` | | Comma-separated file globs — **forces naming-only mode** (ignores `--checks` and `--profile`) | — |
| `--profile` | | Lint profile (`default`, `full`, `perspective-only`, `scripts-only`, `naming-only`) | `default` |
| `--checks` | | Comma-separated list of checks: `perspective`, `naming`, `scripts` | per profile |
| `--naming-only` | | Only run naming convention checks | `false` |
| `--component-style` | | Naming style for components | `PascalCase` |
| `--parameter-style` | | Naming style for parameters | `camelCase` |
| `--component-style-rgx` | | Custom regex for component names | — |
| `--parameter-style-rgx` | | Custom regex for parameter names | — |
| `--allow-acronyms` | | Allow acronyms in names | `false` |
| `--component` | `-c` | Filter Perspective linting to a component type prefix | — |
| `--schema-mode` | | Schema strictness: `strict`, `robust`, `permissive` | `robust` |
| `--verbose` | `-v` | Show detailed output | `false` |
| `--report-format` | | Output format: `text` or `json` | `text` |
| `--fail-on` | | Minimum severity that causes a non-zero exit code: `error`, `warning`, `info`, `style` | `error` |
| `--ignore-codes` | | Comma-separated rule codes to suppress | — |
| `--ignore-file` | | Path to ignore file (defaults to `.ignition-lintignore` in the project or target root, if it exists) | — |
| `--check-linter` | | Verify that Perspective schema files are available for the current `--schema-mode` and exit (useful for CI setup validation) | — |

### Option precedence

One of `--files`, `--target`, or `--project` is required. They are evaluated in this order:

1. **`--files`** — naming-only mode. All other check options (`--checks`, `--profile`, `--naming-only`) are ignored.
2. **`--target`** — recursive directory mode. Respects `--checks` and `--profile`.
3. **`--project`** — standard Ignition layout mode. Respects `--checks` and `--profile`.

### `--project` vs `--target`

- **`--project`** expects the standard Ignition project layout and looks for `com.inductiveautomation.perspective/views/` and `ignition/script-python/` subdirectories.
- **`--target`** accepts **any** directory and recursively discovers `view.json` and `.py` files wherever they appear. This is the preferred mode for AI agents, MCP integrations, and ad-hoc linting of subdirectories.

## Naming Styles

| Style | Pattern | Example |
|---|---|---|
| `PascalCase` | Each word capitalized, no separators | `UserStatusLabel` |
| `camelCase` | First word lowercase, rest capitalized | `userStatusLabel` |
| `snake_case` | All lowercase, underscore separators | `user_status_label` |
| `UPPER_SNAKE_CASE` | All uppercase, underscore separators | `USER_STATUS_LABEL` |
| Custom regex | Any pattern via `--component-style-rgx` | — |

## Examples

### Lint any directory recursively

```bash
# Lint everything under a directory (finds view.json and .py files automatically)
ignition-lint --target /path/to/any/folder

# Lint only Perspective views in a subdirectory
ignition-lint -t /path/to/views/ScheduleManagement --checks perspective

# Lint only scripts, output as JSON for AI agent consumption
ignition-lint -t /path/to/scripts --checks scripts --report-format json
```

### Full project lint (standard Ignition layout)

```bash
ignition-lint --project /path/to/project --profile full
```

### Naming only with custom styles

```bash
ignition-lint \
  --files "**/view.json" \
  --component-style PascalCase \
  --parameter-style camelCase \
  --allow-acronyms
```

### Filter by component type

```bash
ignition-lint \
  --project /path/to/project \
  --profile full \
  --component ia.display.label
```

### JSON output for programmatic use

```bash
ignition-lint -t /path/to/project --report-format json
```

### Suppress rules during adoption

```bash
ignition-lint -p ./project --profile full \
  --ignore-codes NAMING_PARAMETER,NAMING_COMPONENT,MISSING_DOCSTRING,LONG_LINE
```

### Verbose output

```bash
ignition-lint --project /path/to/project --profile full --verbose
```

## Understanding the Report

### Summary Section

```text
============================================================
📊 LINT RESULTS
============================================================
📋 Issues by severity:
  ❌ Error: 3
  ⚠️ Warning: 12
  ℹ️ Info: 5
  💡 Style: 8
```

### Issue Details

```text
❌ [SCHEMA_VALIDATION] fontSize should be string not number
   File: path/to/view.json
   Component: ia.display.label at root.children[0]
   Suggestion: Path: props.textStyle.fontSize
```

Each issue includes:
- **Severity + Code** — severity icon and rule identifier (e.g. `❌ [SCHEMA_VALIDATION]`)
- **Message** — description of the problem
- **File path** — exact location of the problematic file (with line number if available)
- **Component path** — location within the view structure (if applicable)
- **Suggestion** — specific guidance for resolution (if available)

### Suppression Summary

When rules are suppressed, the report includes a count:

```
🔇 716 issues suppressed
```

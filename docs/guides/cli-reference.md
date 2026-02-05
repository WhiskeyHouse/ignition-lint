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
| `--files` | | Comma-separated file globs for naming-only linting | — |
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
| `--fail-on` | | Severity threshold for non-zero exit: `error`, `warning`, `info`, `style` | `error` |
| `--ignore-codes` | | Comma-separated rule codes to suppress | — |
| `--ignore-file` | | Path to ignore file | `.ignition-lintignore` |
| `--check-linter` | | Verify schema assets are available and exit | — |

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

```
📊 LINT RESULTS
============================================================
📁 Files processed: 226
🧩 Components analyzed: 2,660
✅ Valid components: 2,533 (95.2%)
❌ Invalid components: 127
📈 Schema compliance: 95.2%
```

### Issue Details

```
📄 path/to/view.json
   ❌ SCHEMA_VALIDATION: fontSize should be string not number
      Component: ia.display.label at root.children[0]
      Suggestion: Path: props.textStyle.fontSize
```

Each issue includes:
- **File path** — exact location of the problematic file
- **Severity + Code** — issue category and rule identifier
- **Message** — description of the problem
- **Component path** — location within the view structure
- **Suggestion** — specific guidance for resolution

### Suppression Summary

When rules are suppressed, the report includes a count:

```
🔇 716 issues suppressed
```

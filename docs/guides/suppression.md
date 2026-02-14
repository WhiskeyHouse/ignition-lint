---
sidebar_position: 3
title: Suppression
---

# Lint Suppression Guide

Control which rules fire and where. Ignition Lint provides three complementary suppression mechanisms, each suited to a different scope:

| Mechanism | Scope | Applies To | How |
|---|---|---|---|
| `--ignore-codes` | Global | All files | CLI flag / env var |
| `.ignition-lintignore` | Per-project | File path patterns | Gitignore-style file |
| Inline comments | Per-line / per-file | Python scripts only | Source comments |

All three mechanisms stack: an issue is suppressed if **any** mechanism matches it.

---

## 1. `--ignore-codes` CLI Flag

Suppress one or more rule codes globally across the entire run.

```bash
# Single code
ignition-lint -p /path/to/project --ignore-codes NAMING_PARAMETER

# Multiple codes (comma-separated, no spaces)
ignition-lint -p /path/to/project --ignore-codes NAMING_PARAMETER,NAMING_COMPONENT,LONG_LINE
```

### GitHub Actions

```yaml
- uses: TheThoughtagen/ignition-lint@v1
  with:
    project_path: ./my-project
    ignore_codes: "NAMING_PARAMETER,NAMING_COMPONENT"
```

### MCP Server

All MCP tool functions accept an optional `ignore_codes` parameter:

```python
lint_ignition_project(
    project_path="/path/to/project",
    ignore_codes="NAMING_PARAMETER,LONG_LINE",
)
```

### Environment Variable (Actions entry point)

```bash
export INPUT_IGNORE_CODES="NAMING_PARAMETER,NAMING_COMPONENT"
ignition-lint-action
```

---

## 2. `.ignition-lintignore` File

Place a `.ignition-lintignore` file in the project root directory (the path passed to `--project`). The linter reads it automatically.

### Syntax

Each line is either a **blanket pattern** (suppresses all rules) or a **rule-specific pattern** (suppresses only named codes). Comments and blank lines are ignored.

```gitignore
# Blank lines and lines starting with # are ignored

# Blanket ignore: suppress ALL rules for matching files
scripts/generated/**
tests/fixtures/**

# Rule-specific ignore: suppress only named codes for matching files
com.inductiveautomation.perspective/views/_REFERENCE/**:NAMING_COMPONENT,GENERIC_COMPONENT_NAME
ignition/script-python/legacy/**:MISSING_DOCSTRING,JYTHON_PRINT_STATEMENT
```

### Pattern Format

Patterns use **gitignore / glob** syntax (powered by [pathspec](https://pypi.org/project/pathspec/) with `gitwildmatch` mode):

| Pattern | Matches |
|---|---|
| `*.py` | All `.py` files in the project root |
| `**/*.py` | All `.py` files at any depth |
| `scripts/generated/**` | Everything under `scripts/generated/` |
| `views/_REF*/` | Directories starting with `_REF` under `views/` |

### Rule-Specific Format

Append `:CODE1,CODE2` after the pattern (no spaces around the colon):

```
pattern:CODE1,CODE2
```

A line **without** a colon is treated as a blanket pattern. A line **with** a colon splits into a path pattern and a set of codes.

### Custom File Location

Override the default location with `--ignore-file`:

```bash
ignition-lint -p /path/to/project --ignore-file /shared/config/.ignition-lintignore
```

### Path Resolution

Paths are matched relative to the project root. Given `--project /home/user/my-project`, the pattern `scripts/generated/**` matches files under `/home/user/my-project/scripts/generated/`.

---

## 3. Inline Comments (Python Scripts Only)

Suppress specific rules directly in `.py` source files. This mechanism only applies to standalone Python scripts in `script-python` directories. It does **not** apply to `view.json` files or inline Jython snippets.

### Directives

| Directive | Scope | Placement |
|---|---|---|
| `disable-file=CODES` | Entire file | Must appear in the **first 10 lines** |
| `disable-next=CODES` | Next line only | Line immediately before the target |
| `disable-line=CODES` | Current line | On the same line as the target |
| `disable=CODES` | Current line | Shorthand for `disable-line` |

All directives use the prefix `# ignition-lint:` followed by the directive and a comma-separated list of rule codes.

### Examples

#### Suppress for an entire file

```python
# ignition-lint: disable-file=MISSING_DOCSTRING

def get_tag_value(path):
    return system.tag.readBlocking([path])[0].value

def set_tag_value(path, value):
    system.tag.writeBlocking([path], [value])
```

#### Suppress on a single line

```python
x = build_very_long_configuration_string(a, b, c, d)  # ignition-lint: disable=LONG_LINE
```

#### Suppress on the next line

```python
# ignition-lint: disable-next=IGNITION_SYSTEM_OVERRIDE
system = get_custom_proxy()  # intentional override for testing
```

#### Suppress multiple rules

```python
# ignition-lint: disable-file=MISSING_DOCSTRING,LONG_LINE
```

### Behavior Notes

- `disable-file` is only recognised in the **first 10 lines** of the file.
- `disable-next` applies to exactly one line following the comment.
- Multiple directives can coexist in the same file.
- `FILE_READ_ERROR` cannot be suppressed inline (it fires before parsing).

---

## Report Output

When issues are suppressed, the report summary includes a suppression count:

```
📊 LINT RESULTS
============================================================
📋 Issues by severity:
  ❌ Error: 117
  ⚠️ Warning: 285
  ℹ️ Info: 702
  💡 Style: 865

🔇 716 issues suppressed
```

Inline comment suppressions happen inside the script linter before issues reach the report, so they are not included in the `🔇` count.

---

## Examples

### Gradual Adoption

Suppress noisy rules during initial rollout, then remove suppressions as the codebase improves:

```bash
# Phase 1: Focus on errors only
ignition-lint -p ./my-project --profile full \
  --ignore-codes NAMING_PARAMETER,NAMING_COMPONENT,MISSING_DOCSTRING,LONG_LINE,GENERIC_COMPONENT_NAME

# Phase 2: Address naming
ignition-lint -p ./my-project --profile full \
  --ignore-codes MISSING_DOCSTRING,LONG_LINE

# Phase 3: Full enforcement
ignition-lint -p ./my-project --profile full
```

### Ignore Generated / Reference Views

```gitignore
# .ignition-lintignore
com.inductiveautomation.perspective/views/_generated/**
com.inductiveautomation.perspective/views/_REFERENCE/**:NAMING_COMPONENT,GENERIC_COMPONENT_NAME
ignition/script-python/legacy/**:MISSING_DOCSTRING
```

### CI Pipeline with Selective Suppression

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
          ignore_codes: "NAMING_PARAMETER"
          fail_on: error
```

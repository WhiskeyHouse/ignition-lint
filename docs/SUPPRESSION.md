# Lint Suppression Guide

> **Note:** The canonical version of this guide is [docs/guides/suppression.md](./guides/suppression.md). This file is kept for backwards compatibility.

Control which rules fire and where. Ignition Lint provides three complementary suppression mechanisms, each suited to a different scope:

| Mechanism | Scope | Applies To | How |
|-----------|-------|------------|-----|
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
- uses: whiskeyhouse/ignition-lint@v1
  with:
    project_path: ./my-project
    ignore_codes: "NAMING_PARAMETER,NAMING_COMPONENT"
```

### MCP Server

All MCP tool functions accept an optional `ignore_codes` parameter:

```python
# Example: calling the lint_ignition_project MCP tool
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

Patterns use **gitignore / glob** syntax (powered by the [pathspec](https://pypi.org/project/pathspec/) library with `gitwildmatch` mode):

| Pattern | Matches |
|---------|---------|
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

### Explicit File Path

Override the default location with `--ignore-file`:

```bash
ignition-lint -p /path/to/project --ignore-file /shared/config/.ignition-lintignore
```

### Path Resolution

Paths in the ignore file are matched relative to the project root. For example, given `--project /home/user/my-project`, the pattern `scripts/generated/**` matches files under `/home/user/my-project/scripts/generated/`.

---

## 3. Inline Comments (Python Scripts Only)

Suppress specific rules directly in `.py` source files. This mechanism only applies to standalone Python scripts in `script-python` directories. It does **not** apply to `view.json` files (comments are invalid JSON) or inline Jython snippets (stored as JSON strings).

### Comment Directives

| Directive | Scope | Placement |
|-----------|-------|-----------|
| `disable-file=CODES` | Entire file | Must appear in the **first 10 lines** |
| `disable-next=CODES` | Next line only | Line immediately before the target |
| `disable-line=CODES` | Current line | On the same line as the target |
| `disable=CODES` | Current line | Shorthand for `disable-line` |

All directives use the prefix `# ignition-lint:` followed by the directive and a comma-separated list of rule codes.

### Examples

#### Suppress a rule for the entire file

```python
# ignition-lint: disable-file=MISSING_DOCSTRING
# This legacy module predates our docstring requirements.

def get_tag_value(path):
    return system.tag.readBlocking([path])[0].value

def set_tag_value(path, value):
    system.tag.writeBlocking([path], [value])
```

#### Suppress a rule on a single line

```python
x = build_very_long_configuration_string(param_a, param_b, param_c, param_d)  # ignition-lint: disable=LONG_LINE
```

#### Suppress a rule on the next line

```python
# ignition-lint: disable-next=IGNITION_SYSTEM_OVERRIDE
system = get_custom_proxy()  # intentional override for testing
```

#### Suppress multiple rules

```python
# ignition-lint: disable-file=MISSING_DOCSTRING,LONG_LINE
```

```python
x = 1  # ignition-lint: disable=LONG_LINE,JYTHON_PRINT_STATEMENT
```

### Behavior Notes

- `disable-file` is only recognised if it appears within the **first 10 lines** of the file. Comments placed later are silently ignored.
- `disable-next` applies to exactly the line immediately following the comment. It does not cascade.
- Multiple directives can coexist in the same file.
- The `FILE_READ_ERROR` code cannot be suppressed via inline comments (it fires before the file content is parsed).

---

## Rule Code Reference

Below is a non-exhaustive list of rule codes you can suppress. Run the linter with `--report-format json` to see the exact codes produced for your project.

### Perspective / Schema Rules

| Code | Severity | Description |
|------|----------|-------------|
| `SCHEMA_VALIDATION` | ERROR | Component structure doesn't match schema |
| `GENERIC_COMPONENT_NAME` | STYLE | Component has a non-descriptive default name |
| `MISSING_ICON_PATH` | WARNING | Icon component missing required path prop |
| `SINGLE_CHILD_FLEX` | STYLE | Flex container with only one child |

### Naming Rules

| Code | Severity | Description |
|------|----------|-------------|
| `NAMING_COMPONENT` | STYLE | Component name doesn't match naming style |
| `NAMING_PARAMETER` | STYLE | Parameter or custom property key doesn't match naming style |

### Script Rules

| Code | Severity | Description |
|------|----------|-------------|
| `SYNTAX_ERROR` | ERROR | Python syntax error |
| `FILE_READ_ERROR` | ERROR | Could not read file |
| `LONG_LINE` | STYLE | Line exceeds 120 characters |
| `MISSING_DOCSTRING` | STYLE | Public function missing docstring |
| `GLOBAL_VARIABLE_USAGE` | WARNING | `global` keyword usage |
| `JYTHON_PRINT_STATEMENT` | WARNING | `print x` statement syntax |
| `JYTHON_DEPRECATED_ITERITEMS` | WARNING | `.iteritems()` usage |
| `JYTHON_XRANGE_USAGE` | INFO | `xrange()` usage |
| `JYTHON_STRING_TYPES` | WARNING | `basestring`/`unicode` usage |
| `IGNITION_SYSTEM_OVERRIDE` | ERROR | Overriding `system` variable |
| `IGNITION_HARDCODED_GATEWAY` | WARNING | Hardcoded gateway URL |
| `IGNITION_DEBUG_PRINT` | INFO | Debug print statement |
| `IGNITION_UNKNOWN_SYSTEM_CALL` | WARNING | Unrecognised `system.*` call |
| `JAVA_INTEGRATION_DETECTED` | INFO | Java imports present |
| `PARSE_WARNING` | WARNING | File could not be fully parsed |

### Jython Inline Rules (from view.json scripts)

| Code | Severity | Description |
|------|----------|-------------|
| `JYTHON_SYNTAX_ERROR` | ERROR | Syntax error in inline script |
| `JYTHON_IGNITION_INDENTATION_REQUIRED` | ERROR | Missing required indentation |
| `JYTHON_PRINT_STATEMENT` | WARNING | Print statement in inline script |
| `JYTHON_PREFER_PERSPECTIVE_PRINT` | INFO | Prefer `system.perspective.print()` |

---

## Report Output

When issues are suppressed, the report summary includes a suppression count:

```
============================================================
📊 LINT RESULTS
============================================================
📋 Issues by severity:
  ❌ Error: 117
  ⚠️ Warning: 285
  ℹ️ Info: 702
  💡 Style: 865

🔇 716 issues suppressed

[... detailed issue list ...]
```

If all issues are suppressed:

```
============================================================
📊 LINT RESULTS
============================================================
✅ No issues found
🔇 2685 issues suppressed
```

The suppressed count reflects issues matched by `--ignore-codes` or `.ignition-lintignore`. Inline comment suppressions happen inside the script linter before issues reach the report, so they are not included in this count.

---

## Examples

### Gradual Adoption

Suppress noisy rules during initial rollout, then remove suppressions as the codebase is cleaned up:

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

```
# .ignition-lintignore
# Auto-generated views from Designer templates
com.inductiveautomation.perspective/views/_generated/**

# Reference/template views exempt from naming rules
com.inductiveautomation.perspective/views/_REFERENCE/**:NAMING_COMPONENT,GENERIC_COMPONENT_NAME

# Legacy scripts pre-dating docstring requirements
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
      - uses: whiskeyhouse/ignition-lint@v1
        with:
          project_path: .
          lint_type: all
          ignore_codes: "NAMING_PARAMETER"
          fail_on: error
```

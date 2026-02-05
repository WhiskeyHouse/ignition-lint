---
sidebar_position: 2
title: Rule Codes
---

# Rule Code Reference

Every issue reported by ignition-lint has a rule code. Use these codes with `--ignore-codes`, `.ignition-lintignore`, or inline comment directives to suppress specific rules.

## Perspective / Schema Rules

| Code | Severity | Description |
|---|---|---|
| `SCHEMA_VALIDATION` | ERROR | Component structure doesn't match the expected schema |
| `SCHEMA_VALIDATION_SKIPPED` | WARNING | Schema validation skipped (`jsonschema` package not installed) |
| `INVALID_JSON` | ERROR | File contains invalid JSON |
| `FILE_READ_ERROR` | ERROR | Could not read view file from disk |
| `NO_COMPONENTS` | INFO | No `ia.*` components found in the view |
| `GENERIC_COMPONENT_NAME` | STYLE | Component has a non-descriptive default name (e.g., `Label`, `Button`) |
| `EMPTY_COMPONENT_NAME` | WARNING | Component has an empty or missing `meta.name` |
| `MISSING_META_PROPERTY` | WARNING | Component missing a required meta property (e.g., `name`) |
| `MISSING_ICON_PATH` | ERROR | Icon component missing the required `path` prop |
| `MISSING_LABEL_TEXT` | WARNING | Label component has no `text` prop or text binding |
| `SINGLE_CHILD_FLEX` | STYLE | Flex container with only one child — consider removing the wrapper |
| `MISSING_FLEX_DIRECTION` | INFO | Multi-child flex container without an explicit `direction` prop |
| `MISSING_CHILD_POSITION` | WARNING | Child component inside a container missing `position` properties |
| `PERFORMANCE_CONSIDERATION` | INFO | Component type known to have performance implications |
| `ACCESSIBILITY_LABELING` | INFO | Interactive component may need better labeling for accessibility |
| `INVALID_BINDING_TYPE` | ERROR | Unrecognised binding type in `propConfig` |
| `MISSING_TAG_PATH` | ERROR | Tag binding missing required `tagPath` |
| `MISSING_TAG_FALLBACK` | INFO | Tag binding on a critical prop without `fallbackDelay` |
| `MISSING_EXPRESSION` | ERROR | Expression binding missing required `expression` field |
| `MISSING_PROPERTY_PATH` | ERROR | Property binding missing required `path` field |
| `INVALID_TRANSFORM_TYPE` | ERROR | Unrecognised transform type |
| `MISSING_SCRIPT_CODE` | ERROR | Script transform missing `code` property |
| `MISSING_TRANSFORM_EXPRESSION` | ERROR | Expression transform missing `expression` property |
| `MISSING_MAP_MAPPINGS` | WARNING | Map transform missing `mappings` array |
| `MISSING_MAP_FALLBACK` | INFO | Map transform without a `fallback` value |

## Expression Rules

Checks applied to Ignition expression language strings in bindings and transforms.

| Code | Severity | Description |
|---|---|---|
| `EXPR_NOW_DEFAULT_POLLING` | WARNING | `now()` called without arguments — defaults to 1 000 ms polling |
| `EXPR_NOW_LOW_POLLING` | INFO | `now(N)` where N < 5 000 ms — may impact client performance |
| `EXPR_INVALID_PROPERTY_REF` | ERROR | `{...}` property reference contains spaces (malformed path) |
| `EXPR_UNKNOWN_FUNCTION` | INFO | Expression function not in the known Ignition function catalog |
| `EXPR_BAD_COMPONENT_REF` | WARNING | Component tree traversal (`getSibling`, `getParent`, etc.) in an expression — fragile |

## Unused Property Rules

Per-view analysis that detects custom and param properties with no apparent references.

| Code | Severity | Description |
|---|---|---|
| `UNUSED_CUSTOM_PROPERTY` | WARNING | Custom property defined but not referenced in any expression, script, or binding target in the view |
| `UNUSED_PARAM_PROPERTY` | INFO | Param property not referenced within the view (may be set by an embedding view) |

## Naming Rules

| Code | Severity | Description |
|---|---|---|
| `NAMING_COMPONENT` | STYLE | Component name doesn't match the configured naming style |
| `NAMING_PARAMETER` | STYLE | Parameter name doesn't match the configured naming style |
| `NAMING_CUSTOM` | STYLE | Custom property key doesn't match the configured naming style |

## Script Rules (standalone `.py` files)

| Code | Severity | Description |
|---|---|---|
| `SYNTAX_ERROR` | ERROR | Python syntax error |
| `FILE_READ_ERROR` | ERROR | Could not read file from disk |
| `LONG_LINE` | STYLE | Line exceeds 120 characters |
| `MISSING_DOCSTRING` | STYLE | Public function missing a docstring |
| `GLOBAL_VARIABLE_USAGE` | WARNING | Usage of the `global` keyword |
| `JYTHON_PRINT_STATEMENT` | WARNING | `print x` statement syntax (Python 2 style) |
| `JYTHON_DEPRECATED_ITERITEMS` | WARNING | `.iteritems()` usage (removed in Python 3) |
| `JYTHON_XRANGE_USAGE` | INFO | `xrange()` usage (renamed to `range` in Python 3) |
| `JYTHON_STRING_TYPES` | WARNING | `basestring` or `unicode` usage |
| `IGNITION_SYSTEM_OVERRIDE` | ERROR | Overriding the `system` variable |
| `IGNITION_HARDCODED_GATEWAY` | WARNING | Hardcoded gateway URL |
| `IGNITION_DEBUG_PRINT` | INFO | Debug `print()` statement left in code |
| `IGNITION_UNKNOWN_SYSTEM_CALL` | WARNING | Unrecognised `system.*` function call |
| `JAVA_INTEGRATION_DETECTED` | INFO | Java imports present in script |
| `PARSE_WARNING` | WARNING | File could not be fully parsed |

## Jython Inline Rules (from `view.json` script bindings and event handlers)

| Code | Severity | Description |
|---|---|---|
| `JYTHON_SYNTAX_ERROR` | ERROR | Syntax error in an inline script |
| `JYTHON_PARSE_ERROR` | ERROR | Script could not be parsed at all |
| `JYTHON_INDENTATION_REQUIRED` | ERROR | Missing required indentation in inline script |
| `JYTHON_MIXED_INDENTATION` | WARNING | Mixed tabs and spaces on the same line |
| `JYTHON_INCONSISTENT_INDENTATION_STYLE` | INFO | File uses both tabs and spaces for indentation |
| `JYTHON_INDENTATION_JUMP` | ERROR | Indentation increases by more than one level |
| `JYTHON_PRINT_STATEMENT` | WARNING | `print x` statement syntax — use `print()` function |
| `JYTHON_PREFER_PERSPECTIVE_PRINT` | INFO | Prefer `system.perspective.print()` over `print()` in Perspective context |
| `JYTHON_HARDCODED_LOCALHOST` | WARNING | Hardcoded `localhost` or `127.0.0.1` reference |
| `JYTHON_HTTP_WITHOUT_EXCEPTION_HANDLING` | WARNING | HTTP calls without `try/except` error handling |
| `JYTHON_RECOMMEND_ERROR_HANDLING` | INFO | Consider wrapping fragile calls (`getChild`, `sendMessage`, etc.) in error handling |
| `JYTHON_BAD_COMPONENT_REF` | WARNING | Component tree traversal (`getSibling`, `getParent`, `getChild`, `getComponent`) is fragile and breaks on refactoring |

## Usage

### Suppress globally via CLI

```bash
ignition-lint -p ./project --profile full --ignore-codes NAMING_PARAMETER,LONG_LINE
```

### Suppress per-path via `.ignition-lintignore`

```gitignore
views/_REFERENCE/**:NAMING_COMPONENT,GENERIC_COMPONENT_NAME
scripts/legacy/**:MISSING_DOCSTRING
```

### Suppress inline (Python scripts only)

```python
# ignition-lint: disable-file=MISSING_DOCSTRING
# ignition-lint: disable-next=LONG_LINE
x = build_very_long_configuration_string(a, b, c, d)
y = 1  # ignition-lint: disable=JYTHON_PRINT_STATEMENT
```

See the [Suppression Guide](./suppression.md) for the full reference.

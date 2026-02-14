---
sidebar_position: 2
title: Pre-commit
---

# Pre-commit Hook

Run ignition-lint automatically before every commit using [pre-commit](https://pre-commit.com/) or a manual Git hook.

## Using pre-commit framework

Add ignition-lint to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/TheThoughtagen/ignition-lint
    rev: v1  # use a specific tag
    hooks:
      - id: ignition-perspective-lint
```

Then install the hooks:

```bash
pre-commit install
```

### Hook Details

| Field | Value |
|---|---|
| **id** | `ignition-perspective-lint` |
| **name** | Ignition Perspective Linter |
| **entry** | `ignition-lint` |
| **language** | `python` |
| **files** | `\.json$` |
| **args** | `['--format=text', '--severity=warning', '--exit-code']` |

The hook runs on all `.json` files and passes filenames automatically. It exits with a non-zero code if warnings or errors are found, blocking the commit.

### Customizing Arguments

Override the default arguments in your config:

```yaml
repos:
  - repo: https://github.com/TheThoughtagen/ignition-lint
    rev: v1
    hooks:
      - id: ignition-perspective-lint
        args: ['--format=text', '--severity=error', '--exit-code']
```

This only blocks commits on errors (not warnings).

## Manual Git Hook

Alternatively, create a hook script directly:

```bash
#!/bin/sh
# .git/hooks/pre-commit

ignition-lint --project . --profile full > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Ignition lint failed. Run 'ignition-lint --project . --profile full' for details."
    exit 1
fi
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

## Tips

- Use `--ignore-codes` in the hook arguments to suppress rules you haven't addressed yet
- For large projects, consider running the hook only on changed files by using `pass_filenames: true` (the default)
- The pre-commit framework caches environments, so subsequent runs are fast

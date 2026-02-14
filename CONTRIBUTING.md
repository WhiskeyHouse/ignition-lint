# Contributing to ignition-lint

Thanks for your interest in contributing! This guide covers how to get set up and submit changes.

## Getting started

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Clone and install

```bash
git clone https://github.com/TheThoughtagen/ignition-lint.git
cd ignition-lint
uv sync
```

This installs all dependencies (including dev tools) in a virtual environment.

### Verify your setup

```bash
uv run pytest
uv run ignition-lint --help
```

## Development workflow

### Running the linter locally

```bash
# Lint a directory
uv run ignition-lint --target /path/to/ignition/views

# Run with all checks against a full project
uv run ignition-lint --project /path/to/ignition/project --profile full
```

### Running tests

```bash
uv run pytest
```

### Formatting and linting

```bash
uv run black src/ tests/
uv run ruff check src/ tests/
```

## Project structure

```text
src/ignition_lint/
  cli.py                 # CLI entry point
  reporting.py           # LintIssue, LintSeverity, LintReport
  suppression.py         # Suppression config and ignore-file parsing
  json_linter.py         # Perspective view.json linter
  perspective/
    view_model.py        # Flattened ViewModel dataclass
  validators/
    jython.py            # Inline Jython script validation
    expression.py        # Expression language validation
  scripts/
    linter.py            # Standalone .py file linter
  schemas/               # JSON schemas for Ignition components
  server.py              # FastMCP server for AI agent integration
  action_entry.py        # GitHub Action wrapper
tests/                   # Test suite
docs/                    # Documentation (Docusaurus source)
website/                 # Docusaurus site
```

## Making changes

1. **Create a branch** from `main` with a descriptive name.
2. **Make your changes.** Keep commits focused on a single concern.
3. **Add or update tests** for any new functionality or bug fixes.
4. **Run the test suite** to make sure nothing is broken: `uv run pytest`
5. **Format your code**: `uv run black src/ tests/ && uv run ruff check src/ tests/`
6. **Open a pull request** against `main` with a clear description of what changed and why.

## Adding a new lint rule

1. Choose the appropriate module:
   - `json_linter.py` for Perspective/schema rules
   - `validators/jython.py` for inline Jython script rules
   - `validators/expression.py` for expression language rules
   - `scripts/linter.py` for standalone Python script rules
2. Define a rule code constant (e.g., `MY_NEW_RULE = "MY_NEW_RULE"`).
3. Emit issues using `LintIssue` from `reporting.py`.
4. Add tests covering the new rule.
5. Document the rule code in `docs/guides/rule-codes.md`.

## Reporting bugs

Open a [GitHub issue](https://github.com/TheThoughtagen/ignition-lint/issues) with:

- What you expected to happen
- What actually happened
- Steps to reproduce (a minimal `view.json` or `.py` file is ideal)
- Your Python version and ignition-lint version (`ignition-lint --help` shows the version)

## Code of conduct

Be respectful and constructive. We're all here to improve the Ignition developer experience.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

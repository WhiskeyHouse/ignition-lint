#!/usr/bin/env python3
"""Convenience CLI for validating inline Jython scripts.

This wrapper reuses the shared :class:`JythonValidator` implementation so any
updates to the core validator are reflected here automatically. It can validate
standalone scripts or be called from other tooling that wants to lint binding
transforms or event handler payloads.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

from ignition_lint.reporting import LintIssue, LintSeverity
from ignition_lint.validators import JythonValidator

SEVERITY_ICONS = {
    LintSeverity.ERROR: "❌",
    LintSeverity.WARNING: "⚠️",
    LintSeverity.INFO: "ℹ️",
    LintSeverity.STYLE: "💡",
}


def format_script_properly(script: str) -> str:
    """Produce a tab-indented version of the script similar to Ignition's editor."""
    lines = script.split("\n")
    formatted_lines: List[str] = []
    current_indent = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted_lines.append("")
            continue

        if stripped.endswith(":"):
            formatted_lines.append("\t" * current_indent + stripped)
            current_indent += 1
        elif stripped in {"else:", "except:", "finally:"} or stripped.startswith(("elif ", "except ")):
            current_indent = max(0, current_indent - 1)
            formatted_lines.append("\t" * current_indent + stripped)
            if stripped.endswith(":"):
                current_indent += 1
        elif any(stripped.startswith(keyword) for keyword in ("return", "break", "continue", "pass")):
            formatted_lines.append("\t" * current_indent + stripped)
        else:
            original_indent = len(line) - len(line.lstrip("\t"))
            if original_indent < current_indent:
                current_indent = original_indent
            formatted_lines.append("\t" * current_indent + stripped)

    return "\n".join(formatted_lines)


def validate_jython_in_binding(binding_config: dict) -> List[LintIssue]:
    """Validate any script transforms defined in a binding config dictionary."""
    validator = JythonValidator()
    all_issues: List[LintIssue] = []

    for index, transform in enumerate(binding_config.get("transforms", [])):
        if transform.get("type") != "script" or "code" not in transform:
            continue

        issues = validator.validate_script(transform["code"], context=f"transform[{index}]")
        for issue in issues:
            issue.metadata["transformIndex"] = str(index)
        all_issues.extend(issues)

    return all_issues


def validate_jython_in_events(events_config: dict) -> List[LintIssue]:
    """Validate script handlers nested inside an events configuration dictionary."""
    validator = JythonValidator()
    all_issues: List[LintIssue] = []

    for category, handlers in events_config.items():
        if not isinstance(handlers, dict):
            continue

        for name, handler_config in handlers.items():
            handler_list: Iterable[dict] = handler_config if isinstance(handler_config, list) else [handler_config]
            for idx, handler in enumerate(handler_list):
                if not isinstance(handler, dict) or handler.get("type") != "script":
                    continue

                script_code = handler.get("config", {}).get("script", "")
                issues = validator.validate_script(script_code, context=f"events.{category}.{name}[{idx}]")
                for issue in issues:
                    issue.metadata["eventCategory"] = category
                    issue.metadata["eventName"] = name
                    issue.metadata["handlerIndex"] = str(idx)
                all_issues.extend(issues)

    return all_issues


def _print_issues(issues: Iterable[LintIssue]) -> None:
    issues = list(issues)
    if not issues:
        print("✅ No issues found!")
        return

    for issue in issues:
        icon = SEVERITY_ICONS.get(issue.severity, "•")
        line_info = f":{issue.line_number}" if issue.line_number else ""
        print(f"{icon} [{issue.code}] {issue.message}")
        print(f"   Context: {issue.component_path or '<inline>'}")
        print(f"   File: {issue.file_path}{line_info}")
        if issue.suggestion:
            print(f"   💡 {issue.suggestion}")
        if issue.metadata:
            for key, value in issue.metadata.items():
                print(f"   {key}: {value}")
        print()


def _load_script(args: argparse.Namespace) -> tuple[str, str]:
    if args.file:
        path = Path(args.file)
        return path.read_text(), str(path)
    if args.script:
        return args.script, "inline"
    return (
        "\timport json\n\t\n\turl = 'http://127.0.0.1:6000/ask_question'\n\tresponse = system.net.httpClient().post(url)\n",
        "example",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate inline Jython scripts using the shared validator.")
    parser.add_argument("--file", help="Path to a text file containing the script to validate")
    parser.add_argument("--script", help="Script content to validate directly from the command line")
    args = parser.parse_args()

    script, context = _load_script(args)
    validator = JythonValidator()
    issues = validator.validate_script(script, context=context)

    print("🐍 JYTHON VALIDATION RESULTS")
    print("=" * 50)
    _print_issues(issues)

    print("\n🔧 FORMATTED VERSION:")
    print("=" * 50)
    print(format_script_properly(script))

    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())

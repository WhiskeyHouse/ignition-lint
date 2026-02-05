#!/usr/bin/env python3
"""Unified CLI entry point for Ignition linting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

from .json_linter import JsonLinter, ValidationError as NamingError
from .perspective.linter import (
    IgnitionPerspectiveLinter,
    LintIssue as PerspectiveIssue,
    LintSeverity as PerspectiveSeverity,
)
from .reporting import LintIssue, LintReport, LintSeverity, format_report_text
from .schemas import SCHEMA_FILES, schema_path_for
from .scripts.linter import IgnitionScriptLinter, LintSeverity as ScriptSeverity, ScriptLintIssue
from .suppression import build_suppression_config

PROFILE_CHECKS = {
    "default": {"perspective", "naming", "scripts"},
    "perspective-only": {"perspective", "naming"},
    "scripts-only": {"scripts"},
    "naming-only": {"naming"},
    "full": {"perspective", "naming", "scripts"},
}


def check_linter_availability(schema_mode: str) -> bool:
    try:
        path = schema_path_for(schema_mode)
    except ValueError as exc:
        print(f"❌ {exc}")
        return False

    if not path.exists():
        print(f"❌ Schema file not found: {path}")
        return False

    print("✅ Perspective schema available")
    print(f"   Mode: {schema_mode} -> {path}")
    return True


def convert_perspective_issues(issues: Sequence[PerspectiveIssue]) -> Iterable[LintIssue]:
    severity_map = {
        PerspectiveSeverity.ERROR: LintSeverity.ERROR,
        PerspectiveSeverity.WARNING: LintSeverity.WARNING,
        PerspectiveSeverity.INFO: LintSeverity.INFO,
        PerspectiveSeverity.STYLE: LintSeverity.STYLE,
    }
    for issue in issues:
        yield LintIssue(
            severity=severity_map.get(issue.severity, LintSeverity.INFO),
            code=issue.code,
            message=issue.message,
            file_path=issue.file_path,
            component_path=issue.component_path,
            component_type=getattr(issue, "component_type", None),
            suggestion=getattr(issue, "line_suggestion", None),
        )


def convert_script_issues(issues: Sequence[ScriptLintIssue]) -> Iterable[LintIssue]:
    severity_map = {
        ScriptSeverity.ERROR: LintSeverity.ERROR,
        ScriptSeverity.WARNING: LintSeverity.WARNING,
        ScriptSeverity.INFO: LintSeverity.INFO,
        ScriptSeverity.STYLE: LintSeverity.STYLE,
    }
    for issue in issues:
        yield LintIssue(
            severity=severity_map.get(issue.severity, LintSeverity.INFO),
            code=issue.code,
            message=issue.message,
            file_path=issue.file_path,
            line_number=issue.line_number,
            column=issue.column,
            suggestion=issue.suggestion,
        )


def convert_naming_errors(errors: Sequence[NamingError]) -> Iterable[LintIssue]:
    for error in errors:
        location = error.location or "props"
        message = (
            f"{error.error_type.title()} name '{error.name}' does not match {error.expected_style}"
        )
        yield LintIssue(
            severity=LintSeverity.STYLE,
            code=f"NAMING_{error.error_type.upper()}",
            message=message,
            file_path=error.file_path,
            component_path=location,
        )


def lint_perspective(
    target: Path,
    schema_mode: str,
    component_type: Optional[str],
    verbose: bool,
) -> LintReport:
    report = LintReport()
    schema_path = schema_path_for(schema_mode)
    linter = IgnitionPerspectiveLinter(str(schema_path))
    linter.lint_project(str(target), target_component_type=component_type)
    report.extend(convert_perspective_issues(linter.issues))
    return report


def lint_scripts(target: Path, verbose: bool) -> LintReport:
    report = LintReport()
    linter = IgnitionScriptLinter()
    linter.lint_directory(str(target))
    report.extend(convert_script_issues(linter.issues))
    return report


def lint_naming(
    patterns: Iterable[str],
    component_style: str,
    parameter_style: str,
    component_style_rgx: Optional[str],
    parameter_style_rgx: Optional[str],
    allow_acronyms: bool,
) -> LintReport:
    linter = JsonLinter(
        component_style=component_style,
        parameter_style=parameter_style,
        component_style_rgx=component_style_rgx,
        parameter_style_rgx=parameter_style_rgx,
        allow_acronyms=allow_acronyms,
    )
    errors = linter.lint_files(list(patterns))
    report = LintReport()
    report.extend(convert_naming_errors(errors))
    return report


def determine_checks(profile: str, explicit: Optional[str], naming_only: bool) -> Set[str]:
    if explicit:
        return {check.strip().lower() for check in explicit.split(",") if check.strip()}
    if naming_only:
        return {"naming"}
    return PROFILE_CHECKS.get(profile, PROFILE_CHECKS["default"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint Ignition projects using built-in validators", formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--project", "-p", help="Path to Ignition project directory")
    parser.add_argument("--files", help="Comma-separated list of file patterns for naming linting")
    parser.add_argument("--component", "-c", help="Filter Perspective linting to component type prefix")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose diagnostic output")
    parser.add_argument("--schema-mode", choices=SCHEMA_FILES.keys(), default="robust", help="Perspective schema strictness")
    parser.add_argument("--profile", choices=PROFILE_CHECKS.keys(), default="default", help="Preset bundle of checks")
    parser.add_argument("--checks", help="Comma-separated list of checks to run (perspective,naming,scripts)")
    parser.add_argument("--naming-only", action="store_true", help="Only run naming validation")
    parser.add_argument("--component-style", default="PascalCase", help="Naming style for components")
    parser.add_argument("--parameter-style", default="camelCase", help="Naming style for parameters")
    parser.add_argument("--component-style-rgx", help="Custom regex for component names")
    parser.add_argument("--parameter-style-rgx", help="Custom regex for parameter names")
    parser.add_argument("--allow-acronyms", action="store_true", help="Allow acronyms in names")
    parser.add_argument("--report-format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--fail-on", choices=[level.value for level in LintSeverity], default=LintSeverity.ERROR.value, help="Severity threshold that causes a non-zero exit code")
    parser.add_argument("--check-linter", action="store_true", help="Verify schema assets are available and exit")
    parser.add_argument("--ignore-codes", help="Comma-separated rule codes to suppress globally")
    parser.add_argument("--ignore-file", help="Path to ignore file (default: {project}/.ignition-lintignore)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.check_linter:
        return 0 if check_linter_availability(args.schema_mode) else 1

    project_root = Path(args.project).resolve() if args.project else None
    ignore_file = Path(args.ignore_file) if args.ignore_file else None
    suppression = build_suppression_config(
        ignore_codes=args.ignore_codes,
        project_root=project_root,
        ignore_file=ignore_file,
    )
    report = LintReport(suppression=suppression)
    fail_threshold = LintSeverity.from_string(args.fail_on)

    if args.files:
        patterns = [pattern.strip() for pattern in args.files.split(",") if pattern.strip()]
        report.merge(
            lint_naming(
                patterns,
                args.component_style,
                args.parameter_style,
                args.component_style_rgx,
                args.parameter_style_rgx,
                args.allow_acronyms,
            )
        )
    else:
        if not args.project:
            print("❌ Project path is required when --files is not provided")
            return 1

        project_path = Path(args.project).resolve()
        if not project_path.exists():
            print(f"❌ Project path does not exist: {project_path}")
            return 1

        checks = determine_checks(args.profile, args.checks, args.naming_only)

        if "perspective" in checks:
            perspective_path = project_path / "com.inductiveautomation.perspective" / "views"
            if perspective_path.exists():
                report.merge(
                    lint_perspective(
                        perspective_path,
                        args.schema_mode,
                        args.component,
                        args.verbose,
                    )
                )
            else:
                print(f"ℹ️  No Perspective views found at {perspective_path}")

        if "naming" in checks:
            perspective_path = project_path / "com.inductiveautomation.perspective" / "views"
            if perspective_path.exists():
                pattern = str(perspective_path / "**/view.json")
                report.merge(
                    lint_naming(
                        [pattern],
                        args.component_style,
                        args.parameter_style,
                        args.component_style_rgx,
                        args.parameter_style_rgx,
                        args.allow_acronyms,
                    )
                )
            else:
                print("ℹ️  Skipping naming checks (no Perspective views found)")

        if "scripts" in checks:
            scripts_path = project_path / "ignition" / "script-python"
            if scripts_path.exists():
                report.merge(lint_scripts(scripts_path, args.verbose))
            else:
                print(f"ℹ️  No script-python directory found at {scripts_path}")

    if args.report_format == "json":
        output = {
            "issues": [
                {
                    "severity": issue.severity.value,
                    "code": issue.code,
                    "message": issue.message,
                    "file_path": issue.file_path,
                    "component_path": issue.component_path,
                    "component_type": issue.component_type,
                    "line_number": issue.line_number,
                    "column": issue.column,
                    "suggestion": issue.suggestion,
                }
                for issue in report.issues
            ],
            "summary": report.summary,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_report_text(report))

    return 1 if report.has_failures(fail_threshold) else 0


if __name__ == "__main__":
    raise SystemExit(main())

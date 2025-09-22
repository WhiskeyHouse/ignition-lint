#!/usr/bin/env python3
"""GitHub Actions entry point for Ignition Lint using unified CLI helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .cli import (
    LintReport,
    LintSeverity,
    determine_checks,
    format_report_text,
    lint_naming,
    lint_perspective,
    lint_scripts,
)


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes"}


def main() -> None:
    files = os.getenv("INPUT_FILES")
    component_style = os.getenv("INPUT_COMPONENT_STYLE", "PascalCase")
    parameter_style = os.getenv("INPUT_PARAMETER_STYLE", "camelCase")
    component_style_rgx = os.getenv("INPUT_COMPONENT_STYLE_RGX")
    parameter_style_rgx = os.getenv("INPUT_PARAMETER_STYLE_RGX")
    allow_acronyms = env_bool("INPUT_ALLOW_ACRONYMS")
    project_path_env = os.getenv("INPUT_PROJECT_PATH")
    lint_type = os.getenv("INPUT_LINT_TYPE", "perspective")
    naming_only = env_bool("INPUT_NAMING_ONLY", True)
    schema_mode = os.getenv("INPUT_SCHEMA_MODE", "robust")
    fail_on = os.getenv("INPUT_FAIL_ON", LintSeverity.ERROR.value)

    report = LintReport()
    fail_threshold = LintSeverity.from_string(fail_on)

    if project_path_env:
        project_path = Path(project_path_env).resolve()
        if not project_path.exists():
            print(f"❌ Project path does not exist: {project_path}")
            sys.exit(1)

        checks = determine_checks(
            profile="default" if lint_type == "all" else f"{lint_type}-only",
            explicit=None,
            naming_only=naming_only,
        )
        if lint_type == "all" and not naming_only:
            checks = {"perspective", "naming", "scripts"}

        if "perspective" in checks:
            perspective_path = project_path / "com.inductiveautomation.perspective" / "views"
            if perspective_path.exists():
                report.merge(
                    lint_perspective(
                        perspective_path,
                        schema_mode,
                        component_type=os.getenv("INPUT_COMPONENT"),
                        verbose=False,
                    )
                )
            else:
                print(f"ℹ️  No Perspective views found at {perspective_path}")

        if "naming" in checks:
            perspective_path = project_path / "com.inductiveautomation.perspective" / "views"
            if perspective_path.exists():
                report.merge(
                    lint_naming(
                        [str(perspective_path / "**/view.json")],
                        component_style,
                        parameter_style,
                        component_style_rgx,
                        parameter_style_rgx,
                        allow_acronyms,
                    )
                )
            else:
                print("ℹ️  Skipping naming checks (no Perspective views found)")

        if "scripts" in checks:
            scripts_path = project_path / "ignition" / "script-python"
            if scripts_path.exists():
                report.merge(lint_scripts(scripts_path, verbose=False))
            else:
                print(f"ℹ️  No script-python directory found at {scripts_path}")

    elif files:
        patterns = [pattern.strip() for pattern in files.split(",") if pattern.strip()]
        report.merge(
            lint_naming(
                patterns,
                component_style,
                parameter_style,
                component_style_rgx,
                parameter_style_rgx,
                allow_acronyms,
            )
        )
    else:
        print("❌ Either project path or files must be provided")
        sys.exit(1)

    print(format_report_text(report))

    success = not report.has_failures(fail_threshold)
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"result={'success' if success else 'failure'}\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

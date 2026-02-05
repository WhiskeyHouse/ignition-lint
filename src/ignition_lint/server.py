#!/usr/bin/env python3
"""FastMCP server exposing Ignition linting utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - optional dependency
    FastMCP = None

from .cli import (
    LintReport,
    LintSeverity,
    check_linter_availability,
    format_report_text,
    lint_naming,
    lint_perspective,
    lint_scripts,
)
from .schemas import schema_path_for
from .suppression import build_suppression_config

DEFAULT_SCHEMA_MODE = "robust"

if FastMCP is None:
    raise ImportError("fastmcp is required to use ignition_lint.server")

mcp = FastMCP("Ignition Linter")


def _report_to_dict(report: LintReport) -> Dict[str, Any]:
    return {
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


@mcp.resource("ignition://linter/status")
def get_linter_status() -> str:
    """Return JSON status of schema availability."""
    available = check_linter_availability(DEFAULT_SCHEMA_MODE)
    schema_path = schema_path_for(DEFAULT_SCHEMA_MODE)
    return json.dumps(
        {
            "available": available,
            "schema_mode": DEFAULT_SCHEMA_MODE,
            "schema_path": str(schema_path),
        },
        indent=2,
    )


@mcp.resource("ignition://linter/help")
def get_linter_help() -> str:
    """Usage guide for Ignition linter tools."""
    return """
Ignition Linter MCP Tools

Available Tools:
- check_linter_status: Verify schema availability
- lint_perspective_components(project_path, component_type=None)
- lint_jython_scripts(project_path)
- lint_ignition_project(project_path)
- validate_component_json(component, context?) – coming soon
- validate_script_content(script_content, context?) – coming soon
    """.strip()


@mcp.tool()
def check_linter_status() -> str:
    """Check schema availability."""
    available = check_linter_availability(DEFAULT_SCHEMA_MODE)
    schema_path = schema_path_for(DEFAULT_SCHEMA_MODE)
    return json.dumps(
        {
            "available": available,
            "schema_mode": DEFAULT_SCHEMA_MODE,
            "schema_path": str(schema_path),
        },
        indent=2,
    )


@mcp.tool()
def lint_perspective_components(
    project_path: str,
    component_type: Optional[str] = None,
    verbose: bool = False,
    ignore_codes: Optional[str] = None,
) -> str:
    """Lint Perspective components in an Ignition project."""
    perspective_dir = Path(project_path) / "com.inductiveautomation.perspective" / "views"
    if not perspective_dir.exists():
        return f"ℹ️  No Perspective views found at {perspective_dir}"

    suppression = build_suppression_config(
        ignore_codes=ignore_codes,
        project_root=Path(project_path),
    )
    report = LintReport(suppression=suppression)
    report.merge(lint_perspective(perspective_dir, DEFAULT_SCHEMA_MODE, component_type, verbose))
    return format_report_text(report)


@mcp.tool()
def lint_jython_scripts(
    project_path: str,
    verbose: bool = False,
    ignore_codes: Optional[str] = None,
) -> str:
    """Lint Jython/Python scripts in an Ignition project."""
    script_dir = Path(project_path) / "ignition" / "script-python"
    if not script_dir.exists():
        return f"ℹ️  No script-python directory found at {script_dir}"

    suppression = build_suppression_config(
        ignore_codes=ignore_codes,
        project_root=Path(project_path),
    )
    report = LintReport(suppression=suppression)
    report.merge(lint_scripts(script_dir, verbose))
    return format_report_text(report)


@mcp.tool()
def lint_ignition_project(
    project_path: str,
    lint_type: str = "all",
    component_type: Optional[str] = None,
    verbose: bool = False,
    ignore_codes: Optional[str] = None,
) -> str:
    """Comprehensive linting for an Ignition project."""
    root = Path(project_path)
    suppression = build_suppression_config(
        ignore_codes=ignore_codes,
        project_root=root,
    )
    aggregate = LintReport(suppression=suppression)

    if lint_type in {"all", "perspective"}:
        perspective_dir = root / "com.inductiveautomation.perspective" / "views"
        if perspective_dir.exists():
            aggregate.merge(
                lint_perspective(
                    perspective_dir,
                    DEFAULT_SCHEMA_MODE,
                    component_type,
                    verbose,
                )
            )
        else:
            aggregate.merge(LintReport())

    if lint_type in {"all", "naming"}:
        perspective_dir = root / "com.inductiveautomation.perspective" / "views"
        if perspective_dir.exists():
            aggregate.merge(
                lint_naming(
                    [str(perspective_dir / "**/view.json")],
                    component_style="PascalCase",
                    parameter_style="camelCase",
                    component_style_rgx=None,
                    parameter_style_rgx=None,
                    allow_acronyms=False,
                )
            )

    if lint_type in {"all", "scripts"}:
        script_dir = root / "ignition" / "script-python"
        if script_dir.exists():
            aggregate.merge(lint_scripts(script_dir, verbose))

    return format_report_text(aggregate)


if __name__ == "__main__":  # pragma: no cover
    mcp.run()

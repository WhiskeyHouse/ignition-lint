"""Validation helpers for inline Jython/Python scripts in Ignition."""
from __future__ import annotations

import ast
import re
import textwrap
from dataclasses import dataclass
from typing import List, Optional

from ..reporting import LintIssue, LintSeverity


@dataclass
class JythonIssue:
    """Internal representation used before conversion to lint issue."""

    severity: LintSeverity
    code: str
    message: str
    suggestion: Optional[str] = None
    line_number: Optional[int] = None


class JythonValidator:
    """Validates inline Jython scripts from Ignition projects."""

    def __init__(self) -> None:
        self.issues: List[JythonIssue] = []

    def validate_script(self, script_content: str, context: str = "script") -> List[LintIssue]:
        """Validate a script and return normalized lint issues."""
        self.issues = []

        if not script_content or not script_content.strip():
            return []

        self._check_indentation(script_content, context)
        self._check_syntax(script_content, context)
        self._check_ignition_patterns(script_content, context)

        lint_issues: List[LintIssue] = []
        for issue in self.issues:
            lint_issues.append(
                LintIssue(
                    severity=issue.severity,
                    code=issue.code,
                    message=issue.message,
                    file_path="<inline>",
                    component_path=context,
                    line_number=issue.line_number,
                    suggestion=issue.suggestion,
                )
            )
        return lint_issues

    def _check_indentation(self, script: str, context: str) -> None:
        lines = script.split("\n")
        mixed_lines = []
        tab_lines = []
        space_lines = []
        non_indented = []
        inconsistent_levels = []

        previous_indent = 0

        for index, line in enumerate(lines, 1):
            if not line.strip():
                continue

            tabs = len(line) - len(line.lstrip("\t"))
            line_after_tabs = line.lstrip("\t")
            spaces_after_tabs = len(line_after_tabs) - len(line_after_tabs.lstrip(" "))
            total_spaces = len(line) - len(line.lstrip(" "))

            if not line.startswith("\t") and not line.startswith("    "):
                non_indented.append(index)

            if "\t" in line[: tabs + spaces_after_tabs]:
                if spaces_after_tabs > 0:
                    mixed_lines.append(index)
                else:
                    tab_lines.append((index, tabs))
            elif total_spaces > 0:
                space_lines.append((index, total_spaces))

            current_indent = tabs + (spaces_after_tabs // 4)
            if current_indent > previous_indent + 1:
                inconsistent_levels.append((index, current_indent, previous_indent))
            previous_indent = current_indent

        if non_indented:
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.ERROR,
                    code="JYTHON_INDENTATION_REQUIRED",
                    message=(
                        f"Lines {non_indented[:5]} have no indentation - Ignition requires at least one tab or 4 spaces"
                    ),
                    suggestion="Indent each line with a tab (recommended) or 4 spaces.",
                    line_number=non_indented[0],
                )
            )

        for line_num in mixed_lines[:3]:
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.WARNING,
                    code="JYTHON_MIXED_INDENTATION",
                    message=f"Mixed tabs and spaces on line {line_num}",
                    suggestion="Use consistent tabs for indentation (Ignition standard).",
                    line_number=line_num,
                )
            )

        if space_lines and tab_lines:
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.INFO,
                    code="JYTHON_INCONSISTENT_INDENTATION_STYLE",
                    message="Mixed indentation styles detected (tabs and spaces).",
                    suggestion="Use tabs consistently to match Ignition conventions.",
                )
            )

        for line_num, current, previous in inconsistent_levels:
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.ERROR,
                    code="JYTHON_INDENTATION_JUMP",
                    message=f"Indentation jumps from {previous} to {current} levels on line {line_num}.",
                    suggestion="Increase indentation by one level per logical block.",
                    line_number=line_num,
                )
            )

    def _check_syntax(self, script: str, context: str) -> None:
        # Ignition stores inline scripts with leading indentation; dedent before parsing
        dedented = textwrap.dedent(script)
        try:
            ast.parse(dedented)
        except SyntaxError as exc:
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.ERROR,
                    code="JYTHON_SYNTAX_ERROR",
                    message=f"Python syntax error: {exc.msg}",
                    suggestion=f"Fix syntax near line {exc.lineno}.",
                    line_number=exc.lineno or 1,
                )
            )
        except Exception as exc:
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.ERROR,
                    code="JYTHON_PARSE_ERROR",
                    message=f"Could not parse script: {exc}",
                    suggestion="Check script for syntax issues.",
                )
            )

    def _check_ignition_patterns(self, script: str, context: str) -> None:
        if "localhost" in script or "127.0.0.1" in script:
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.WARNING,
                    code="JYTHON_HARDCODED_LOCALHOST",
                    message="Hardcoded localhost reference detected.",
                    suggestion="Use a configurable gateway URL.",
                )
            )

        # Flag print statement syntax (print x) — should use print() function
        if re.search(r"\bprint\s+[^(]", script):
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.WARNING,
                    code="JYTHON_PRINT_STATEMENT",
                    message="Print statement found - use print() function for Jython compatibility.",
                    suggestion="Change 'print x' to 'print(x)'",
                )
            )

        # Suggest system.perspective.print() over bare print() in Perspective scripts
        if re.search(r"\bprint\s*\(", script) and "system.perspective.print" not in script:
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.INFO,
                    code="JYTHON_PREFER_PERSPECTIVE_PRINT",
                    message="Consider using system.perspective.print() for Perspective logging.",
                    suggestion="Replace print() with system.perspective.print() for gateway log visibility",
                )
            )

        if ("httpClient" in script or "httpPost" in script or "httpGet" in script) and (
            "try:" not in script or "except" not in script
        ):
            self.issues.append(
                JythonIssue(
                    severity=LintSeverity.WARNING,
                    code="JYTHON_HTTP_WITHOUT_EXCEPTION_HANDLING",
                    message="HTTP calls should be wrapped in try/except blocks.",
                    suggestion="Add error handling around network calls.",
                )
            )

        for func in ["getChild", "getSibling", "sendMessage", "closePopup"]:
            if func in script and "try:" not in script:
                self.issues.append(
                    JythonIssue(
                        severity=LintSeverity.INFO,
                        code="JYTHON_RECOMMEND_ERROR_HANDLING",
                        message=f"Consider wrapping {func} usage in error handling.",
                    )
                )

        # Flag fragile component tree traversal
        for func in ["getSibling", "getParent", "getChild", "getComponent"]:
            if re.search(rf"\b{func}\s*\(", script):
                self.issues.append(
                    JythonIssue(
                        severity=LintSeverity.WARNING,
                        code="JYTHON_BAD_COMPONENT_REF",
                        message=f"Component tree traversal '{func}()' is fragile and breaks on refactoring",
                        suggestion="Use view custom properties or message handlers instead",
                    )
                )

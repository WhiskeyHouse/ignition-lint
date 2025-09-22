"""Common reporting utilities for Ignition linting."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional


class LintSeverity(str, Enum):
    """Supported issue severities."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STYLE = "style"

    @classmethod
    def ordered_levels(cls) -> List["LintSeverity"]:
        """Severity levels from most to least critical."""
        return [cls.ERROR, cls.WARNING, cls.INFO, cls.STYLE]

    @classmethod
    def from_string(cls, value: str) -> "LintSeverity":
        normalized = value.strip().lower()
        for level in cls:
            if level.value == normalized:
                return level
        raise ValueError(f"Unknown severity level: {value}")

    def fails_threshold(self, threshold: "LintSeverity") -> bool:
        """Return True if this severity should fail given threshold."""
        order = self.ordered_levels()
        return order.index(self) <= order.index(threshold)


@dataclass
class LintIssue:
    """Normalized lint issue structure."""

    severity: LintSeverity
    code: str
    message: str
    file_path: str
    component_path: Optional[str] = None
    component_type: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class LintReport:
    """Aggregate linting results used across modules."""

    issues: List[LintIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def add_issue(self, issue: LintIssue) -> None:
        self.issues.append(issue)
        self.summary[issue.severity.value] = self.summary.get(issue.severity.value, 0) + 1

    def extend(self, issues: Iterable[LintIssue]) -> None:
        for issue in issues:
            self.add_issue(issue)

    def has_failures(self, threshold: LintSeverity) -> bool:
        return any(issue.severity.fails_threshold(threshold) for issue in self.issues)

    def merge(self, other: "LintReport") -> None:
        self.extend(other.issues)
        for severity, count in other.summary.items():
            self.summary[severity] = self.summary.get(severity, 0) + count


def format_report_text(report: LintReport) -> str:
    """Pretty-print a lint report."""
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append("📊 LINT RESULTS")
    lines.append("=" * 60)

    if not report.issues:
        lines.append("✅ No issues found")
        return "\n".join(lines)

    severity_order = LintSeverity.ordered_levels()
    lines.append("📋 Issues by severity:")
    for level in severity_order:
        count = report.summary.get(level.value, 0)
        if count:
            icon = {
                LintSeverity.ERROR: "❌",
                LintSeverity.WARNING: "⚠️",
                LintSeverity.INFO: "ℹ️",
                LintSeverity.STYLE: "💡",
            }[level]
            lines.append(f"  {icon} {level.value.title()}: {count}")

    lines.append("")
    for issue in report.issues:
        icon = {
            LintSeverity.ERROR: "❌",
            LintSeverity.WARNING: "⚠️",
            LintSeverity.INFO: "ℹ️",
            LintSeverity.STYLE: "💡",
        }[issue.severity]
        location = issue.component_path or ""
        line_info = f":{issue.line_number}" if issue.line_number else ""
        lines.append(f"{icon} [{issue.code}] {issue.message}")
        lines.append(f"   File: {issue.file_path}{line_info}")
        if location:
            lines.append(f"   Component: {location}")
        if issue.suggestion:
            lines.append(f"   Suggestion: {issue.suggestion}")
        if issue.metadata:
            for key, value in issue.metadata.items():
                lines.append(f"   {key}: {value}")
        lines.append("")

    return "\n".join(lines).rstrip()

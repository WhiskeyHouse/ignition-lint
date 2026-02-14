"""Validation helpers for inline Jython/Python scripts in Ignition."""

from __future__ import annotations

import ast
import re
import textwrap
from dataclasses import dataclass

from ..reporting import LintIssue, LintSeverity

# Known Java packages available in Ignition's Jython runtime.
# This is a lightweight subset — just enough to distinguish real packages from typos.
KNOWN_JAVA_PACKAGES: frozenset[str] = frozenset(
    {
        # Java standard library
        "java.lang",
        "java.lang.management",
        "java.util",
        "java.util.concurrent",
        "java.util.concurrent.atomic",
        "java.util.concurrent.locks",
        "java.util.function",
        "java.util.regex",
        "java.util.stream",
        "java.util.zip",
        "java.io",
        "java.net",
        "java.math",
        "java.time",
        "java.time.format",
        "java.time.temporal",
        "java.sql",
        "java.text",
        "java.nio",
        "java.nio.charset",
        "java.nio.channels",
        "java.nio.file",
        "java.security",
        "java.security.cert",
        "java.security.interfaces",
        "java.awt",
        "java.awt.datatransfer",
        "java.awt.event",
        "java.awt.geom",
        "javax.swing",
        "javax.swing.border",
        "javax.swing.table",
        "javax.crypto",
        "javax.imageio",
        "javax.naming.ldap",
        "javax.net.ssl",
        "javax.security.auth.x500",
        "javax.servlet",
        "javax.servlet.http",
        "javax.xml.parsers",
        # Ignition SDK — common
        "com.inductiveautomation.ignition.common",
        "com.inductiveautomation.ignition.common.document",
        "com.inductiveautomation.ignition.common.execution",
        "com.inductiveautomation.ignition.common.execution.impl",
        "com.inductiveautomation.ignition.common.logging",
        "com.inductiveautomation.ignition.common.model",
        "com.inductiveautomation.ignition.common.model.values",
        "com.inductiveautomation.ignition.common.script",
        "com.inductiveautomation.ignition.common.script.builtin",
        "com.inductiveautomation.ignition.common.tags.browsing",
        "com.inductiveautomation.ignition.common.user",
        "com.inductiveautomation.ignition.common.util",
        "com.inductiveautomation.ignition.common.util.logutil",
        # Ignition SDK — gateway
        "com.inductiveautomation.ignition.gateway",
        "com.inductiveautomation.ignition.gateway.datasource",
        # Ignition SDK — designer
        "com.inductiveautomation.ignition.designer",
        # Ignition SDK — client
        "com.inductiveautomation.ignition.client.images",
        # Ignition SDK — Perspective
        "com.inductiveautomation.perspective.common",
        "com.inductiveautomation.perspective.gateway",
        # Ignition SDK — Vision (FactoryPMI)
        "com.inductiveautomation.factorypmi.application",
        "com.inductiveautomation.factorypmi.application.components.template",
    }
)


def _preprocess_py2(source: str) -> str:
    """Transform common Python 2 constructs to Python 3 so ast.parse() succeeds.

    Jython in Ignition uses Python 2 syntax.  This avoids spurious
    JYTHON_SYNTAX_ERROR reports for valid Jython code while still letting
    ast.parse() catch genuine errors.
    """
    # print >>stream, args  →  print(args, file=stream)
    source = re.sub(
        r"^(\s*)print[ \t]*>>[ \t]*(\S+)[ \t]*,[ \t]*(.+)$",
        r"\1print(\3, file=\2)",
        source,
        flags=re.MULTILINE,
    )
    # print >>stream  (no args)  →  print(file=stream)
    source = re.sub(
        r"^(\s*)print[ \t]*>>[ \t]*(\S+)[ \t]*$",
        r"\1print(file=\2)",
        source,
        flags=re.MULTILINE,
    )
    # print args  →  print(args)  (skip lines already handled: function calls and >> redirects)
    source = re.sub(
        r"^(\s*)print\b[ \t]+(?!>>)(?!\()(.+)$",
        r"\1print(\2)",
        source,
        flags=re.MULTILINE,
    )
    # except Type, var:  →  except Type as var:
    source = re.sub(
        r"^(\s*except[ \t]+[\w.]+)[ \t]*,[ \t]*(\w+)[ \t]*:",
        r"\1 as \2:",
        source,
        flags=re.MULTILINE,
    )
    # raise Type, value  →  raise Type(value)
    source = re.sub(
        r"^(\s*raise[ \t]+[\w.]+)[ \t]*,[ \t]*(.+)$",
        r"\1(\2)",
        source,
        flags=re.MULTILINE,
    )
    return source


@dataclass
class JythonIssue:
    """Internal representation used before conversion to lint issue."""

    severity: LintSeverity
    code: str
    message: str
    suggestion: str | None = None
    line_number: int | None = None


class JythonValidator:
    """Validates inline Jython scripts from Ignition projects."""

    def __init__(self) -> None:
        self.issues: list[JythonIssue] = []

    def validate_script(
        self, script_content: str, context: str = "script"
    ) -> list[LintIssue]:
        """Validate a script and return normalized lint issues."""
        self.issues = []

        if not script_content or not script_content.strip():
            return []

        self._check_indentation(script_content, context)
        self._check_syntax(script_content, context)
        self._check_ignition_patterns(script_content, context)
        self._check_java_imports(script_content, context)

        lint_issues: list[LintIssue] = []
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
        # Skip indentation heuristics for standalone .py files. Python's own
        # compiler (in _check_syntax) catches real errors; our custom checks
        # are only useful for embedded scripts in JSON event handlers.
        is_standalone = context.endswith(".py") or ".py]" in context
        if is_standalone:
            return

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
        # Transform Python 2 constructs so the Python 3 parser doesn't reject them
        transformed = _preprocess_py2(dedented)
        try:
            ast.parse(transformed)
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
        if re.search(r"(?<![.\w])print\s*\(", script):
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

    # -- Java import checks --------------------------------------------------

    _FROM_IMPORT_RE = re.compile(r"^\s*from\s+([\w.]+)\s+import\s+(.*)", re.MULTILINE)
    _IMPORT_STAR_RE = re.compile(r"^\s*from\s+([\w.]+)\s+import\s+\*", re.MULTILINE)

    def _check_java_imports(self, script: str, context: str) -> None:
        """Flag invalid or suspicious Java import patterns."""
        dedented = textwrap.dedent(script)
        imported_names: list[tuple[str, int]] = []  # (name, line_number)

        for line_num, line in enumerate(dedented.splitlines(), 1):
            stripped = line.strip()

            # Skip comments
            if stripped.startswith("#"):
                continue

            # Check wildcard imports: from java.util import *
            star_match = self._IMPORT_STAR_RE.match(stripped)
            if star_match:
                pkg = star_match.group(1)
                if self._is_java_package(pkg):
                    self.issues.append(
                        JythonIssue(
                            severity=LintSeverity.WARNING,
                            code="JYTHON_IMPORT_STAR",
                            message=f"Wildcard import 'from {pkg} import *' — import specific classes instead",
                            suggestion=f"Replace with explicit imports, e.g. 'from {pkg} import ClassName'",
                            line_number=line_num,
                        )
                    )
                elif self._looks_like_java_package(pkg):
                    # Looks like a Java package but not in known set
                    self.issues.append(
                        JythonIssue(
                            severity=LintSeverity.INFO,
                            code="JYTHON_UNKNOWN_JAVA_PACKAGE",
                            message=f"Unknown Java package '{pkg}' — may be valid but is not recognized",
                            suggestion="Verify the package name is correct",
                            line_number=line_num,
                        )
                    )
                continue

            # Check from ... import ... style
            from_match = self._FROM_IMPORT_RE.match(stripped)
            if from_match:
                pkg = from_match.group(1)
                names_str = from_match.group(2).strip()

                if self._is_java_package(pkg):
                    # Known Java package — collect imported names for unused check
                    for part in names_str.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        # Handle "as" aliases: Exception as JException
                        if " as " in part:
                            _orig, _, alias = part.partition(" as ")
                            imported_names.append((alias.strip(), line_num))
                        else:
                            imported_names.append((part, line_num))
                elif self._looks_like_java_package(pkg):
                    # Looks like a Java package but not in known set
                    self.issues.append(
                        JythonIssue(
                            severity=LintSeverity.INFO,
                            code="JYTHON_UNKNOWN_JAVA_PACKAGE",
                            message=f"Unknown Java package '{pkg}' — may be valid but is not recognized",
                            suggestion="Verify the package name is correct",
                            line_number=line_num,
                        )
                    )

        # Check for unused Java imports
        if imported_names:
            # Build the body text (everything that isn't an import line)
            body_lines = []
            for line in dedented.splitlines():
                stripped = line.strip()
                if stripped.startswith("from ") or stripped.startswith("import "):
                    continue
                body_lines.append(line)
            body = "\n".join(body_lines)

            for name, line_num in imported_names:
                # Check if the name appears anywhere in the non-import body
                if not re.search(rf"\b{re.escape(name)}\b", body):
                    self.issues.append(
                        JythonIssue(
                            severity=LintSeverity.INFO,
                            code="JYTHON_UNUSED_JAVA_IMPORT",
                            message=f"Imported Java class '{name}' is not used in the script",
                            suggestion=f"Remove unused import '{name}'",
                            line_number=line_num,
                        )
                    )

    @staticmethod
    def _is_java_package(pkg: str) -> bool:
        """Check if a package name is in the known Java packages set."""
        return pkg in KNOWN_JAVA_PACKAGES

    @staticmethod
    def _looks_like_java_package(pkg: str) -> bool:
        """Heuristic: does this look like a Java/Ignition package name?"""
        return pkg.startswith(("java.", "javax.", "com.inductiveautomation."))

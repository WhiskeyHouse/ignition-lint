"""Validation helpers for Ignition expression language bindings."""
from __future__ import annotations

import re
from typing import List

from ..reporting import LintIssue, LintSeverity

# Comprehensive catalog of known Ignition expression functions.
# Sourced from Ignition 8.x documentation across all expression categories.
KNOWN_EXPRESSION_FUNCTIONS = frozenset({
    # Math
    "abs", "ceil", "floor", "max", "min", "round", "sqrt", "pow", "log",
    "mod", "rand", "signum",
    # String
    "concat", "endsWith", "indexOf", "left", "len", "lower", "ltrim",
    "mid", "numberFormat", "regexExtract", "repeat", "replace", "reverse",
    "right", "rtrim", "split", "startsWith", "substring", "toStr", "trim",
    "upper", "urlEncode", "urlDecode", "unicodeNormalize",
    # Date/Time
    "dateArith", "dateDiff", "dateExtract", "dateFormat", "dateParse",
    "daysBetween", "hoursBetween", "millisBetween", "minutesBetween",
    "monthsBetween", "now", "secondsBetween", "setTime", "toDate",
    "weeksBetween", "yearsBetween",
    # Logic / Comparison
    "if", "switch", "coalesce", "choose", "isNull", "hasChanged",
    "previousValue", "qualify",
    # Type casting
    "toBool", "toColor", "toDataSet", "toDouble", "toFloat", "toInt",
    "toLong", "toStr", "toDate",
    # Aggregate / Dataset
    "avg", "columnCount", "forEach", "getColumn", "hasRows", "lookup",
    "rowCount", "sum", "dataSetToJSON", "jsonToDataSet",
    # Color
    "chooseColor", "colorMix", "toColor",
    # JSON
    "jsonDecode", "jsonEncode", "jsonMerge", "jsonDelete", "jsonKeys",
    "jsonSet", "jsonLength", "jsonValueByKey",
    # Tag
    "hasQuality", "isGood", "isBad", "isUncertain", "isNotGood",
    "tag", "tagCount",
    # Advanced / Perspective
    "binEncode", "binDecode", "forceQuality", "getMillis", "htmlToPlain",
    "isAuthorized", "mapLat", "mapLng", "runScript",
    "toDataSet", "typeOf",
})

# Pattern to find function calls in Ignition expressions.
# Matches word followed by '(' but not preceded by a dot (to avoid method calls).
_FUNCTION_CALL_RE = re.compile(r"(?<![.\w])([a-zA-Z_]\w*)\s*\(")

# Pattern to find property references like {this.props.value} or {view.custom.x}.
_PROPERTY_REF_RE = re.compile(r"\{([^}]*)\}")

# Component-tree traversal functions that are fragile in expressions.
_BAD_COMPONENT_REF_FUNCS = {"getSibling", "getParent", "getChild", "getComponent"}


class ExpressionValidator:
    """Validates Ignition expression language strings."""

    def validate_expression(
        self,
        expression: str,
        context: str,
        file_path: str,
        component_path: str,
        component_type: str,
    ) -> List[LintIssue]:
        """Validate an Ignition expression and return any issues found."""
        if not expression or not expression.strip():
            return []

        issues: List[LintIssue] = []
        issues.extend(self._check_now_polling(expression, file_path, component_path, component_type))
        issues.extend(self._check_property_references(expression, file_path, component_path, component_type))
        issues.extend(self._check_function_names(expression, file_path, component_path, component_type))
        issues.extend(self._check_bad_component_refs(expression, file_path, component_path, component_type))
        return issues

    def _check_now_polling(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> List[LintIssue]:
        issues: List[LintIssue] = []

        # now() with no args - defaults to 1000ms polling
        for m in re.finditer(r"\bnow\s*\(\s*\)", expression):
            issues.append(LintIssue(
                severity=LintSeverity.WARNING,
                code="EXPR_NOW_DEFAULT_POLLING",
                message="now() without arguments defaults to 1000ms polling; specify an explicit rate",
                file_path=file_path,
                component_path=component_path,
                component_type=component_type,
                suggestion="Use now(5000) or now(0) for event-driven updates",
            ))

        # now(N) with low rate
        for m in re.finditer(r"\bnow\s*\(\s*(\d+)\s*\)", expression):
            rate = int(m.group(1))
            if 0 < rate < 5000:
                issues.append(LintIssue(
                    severity=LintSeverity.INFO,
                    code="EXPR_NOW_LOW_POLLING",
                    message=f"now({rate}) polls at {rate}ms - consider a higher interval for performance",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component_type,
                    suggestion="Rates below 5000ms can impact client performance",
                ))

        return issues

    def _check_property_references(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> List[LintIssue]:
        issues: List[LintIssue] = []

        for m in _PROPERTY_REF_RE.finditer(expression):
            ref = m.group(1).strip()
            # Skip tag paths ([Provider]Path), absolute component paths (/root/...),
            # and relative component paths (.../Component Name/...)
            if ref.startswith("[") or ref.startswith("/") or ref.startswith(".."):
                continue
            # Flag property refs that contain spaces (likely malformed)
            if " " in ref:
                issues.append(LintIssue(
                    severity=LintSeverity.ERROR,
                    code="EXPR_INVALID_PROPERTY_REF",
                    message=f"Property reference '{{{ref}}}' contains spaces",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component_type,
                    suggestion="Remove spaces from property reference path",
                ))

        return issues

    def _check_function_names(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> List[LintIssue]:
        issues: List[LintIssue] = []

        for m in _FUNCTION_CALL_RE.finditer(expression):
            func_name = m.group(1)
            if func_name not in KNOWN_EXPRESSION_FUNCTIONS:
                issues.append(LintIssue(
                    severity=LintSeverity.INFO,
                    code="EXPR_UNKNOWN_FUNCTION",
                    message=f"Unrecognized expression function '{func_name}'",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component_type,
                    suggestion="Check Ignition docs for valid expression functions",
                ))

        return issues

    def _check_bad_component_refs(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> List[LintIssue]:
        issues: List[LintIssue] = []

        for func in _BAD_COMPONENT_REF_FUNCS:
            if re.search(rf"\b{func}\s*\(", expression):
                issues.append(LintIssue(
                    severity=LintSeverity.WARNING,
                    code="EXPR_BAD_COMPONENT_REF",
                    message=f"Component tree traversal '{func}()' in expression is fragile",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component_type,
                    suggestion="Use view custom properties or message handlers instead",
                ))

        return issues

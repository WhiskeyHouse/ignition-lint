"""Validation helpers for Ignition expression language bindings."""

from __future__ import annotations

import re

from ..reporting import LintIssue, LintSeverity

# Comprehensive catalog of known Ignition expression functions.
# Sourced from Ignition 8.x documentation across all expression categories.
KNOWN_EXPRESSION_FUNCTIONS = frozenset(
    {
        # Math
        "abs",
        "ceil",
        "floor",
        "max",
        "min",
        "round",
        "sqrt",
        "pow",
        "log",
        "mod",
        "rand",
        "signum",
        # String
        "concat",
        "endsWith",
        "indexOf",
        "left",
        "len",
        "lower",
        "ltrim",
        "mid",
        "numberFormat",
        "regexExtract",
        "repeat",
        "replace",
        "reverse",
        "right",
        "rtrim",
        "split",
        "startsWith",
        "substring",
        "toStr",
        "toString",
        "trim",
        "upper",
        "urlEncode",
        "urlDecode",
        "unicodeNormalize",
        # Date/Time
        "addDays",
        "addHours",
        "addMillis",
        "addMinutes",
        "addMonths",
        "addSeconds",
        "addWeeks",
        "addYears",
        "dateArith",
        "dateArithmetic",
        "dateDiff",
        "dateExtract",
        "dateFormat",
        "dateParse",
        "daysBetween",
        "getDate",
        "getDayOfMonth",
        "getDayOfWeek",
        "getDayOfYear",
        "getHour",
        "getMillis",
        "getMinute",
        "getMonth",
        "getSecond",
        "getYear",
        "hoursBetween",
        "midnight",
        "millisBetween",
        "minutesBetween",
        "monthsBetween",
        "now",
        "secondsBetween",
        "setTime",
        "toDate",
        "weeksBetween",
        "yearsBetween",
        # Logic / Comparison
        "if",
        "switch",
        "coalesce",
        "choose",
        "isNull",
        "hasChanged",
        "previousValue",
        "qualify",
        "try",
        # Type casting
        "toBool",
        "toBoolean",
        "toColor",
        "toDataSet",
        "toDouble",
        "toFloat",
        "toInt",
        "toLong",
        # Aggregate / Dataset
        "avg",
        "columnCount",
        "columnRearrange",
        "columnRename",
        "forEach",
        "getColumn",
        "hasRows",
        "lookup",
        "rowCount",
        "sum",
        "dataSetToJSON",
        "jsonToDataSet",
        # Color
        "chooseColor",
        "colorMix",
        # JSON
        "jsonDecode",
        "jsonEncode",
        "jsonMerge",
        "jsonDelete",
        "jsonKeys",
        "jsonSet",
        "jsonLength",
        "jsonValueByKey",
        # Tag / Quality
        "hasQuality",
        "isGood",
        "isBad",
        "isUncertain",
        "isNotGood",
        "qualityOf",
        "tag",
        "tagCount",
        # Advanced / Perspective
        "binEncode",
        "binDecode",
        "forceQuality",
        "htmlToPlain",
        "isAuthorized",
        "mapLat",
        "mapLng",
        "runScript",
        "typeOf",
    }
)

# Pattern to find function calls in Ignition expressions.
# Matches word followed by '(' but not preceded by a dot (to avoid method calls).
_FUNCTION_CALL_RE = re.compile(r"(?<![.\w])([a-zA-Z_]\w*)\s*\(")

# Pattern to find property references like {this.props.value} or {view.custom.x}.
_PROPERTY_REF_RE = re.compile(r"\{([^}]*)\}")

# Component-tree traversal functions that are fragile in expressions.
_BAD_COMPONENT_REF_FUNCS = {"getSibling", "getParent", "getChild", "getComponent"}

# Detects array index access OUTSIDE braces, e.g. {view.params.steps}[1]
# This is always invalid — the index must be inside: {view.params.steps[1]}
_EXTERNAL_INDEX_RE = re.compile(r"\{([^}]+)\}\s*\[")

# Detects array index access INSIDE braces, e.g. {view.params.steps[1].complete}
_INTERNAL_INDEX_RE = re.compile(r"\{([^}\[]+)\[")

# Size-guard functions whose result is typically used to protect index access.
_SIZE_GUARD_FUNCS = {"len", "jsonLength", "rowCount", "columnCount"}


def _skip_string(expression: str, start: int) -> tuple[int, bool]:
    """Skip from opening quote to closing quote. Returns (end_pos, closed).

    Ignition expressions use single quotes for strings with no backslash escaping.
    ``start`` must point to the opening ``'``.
    """
    i = start + 1
    while i < len(expression):
        if expression[i] == "'":
            return (i, True)
        i += 1
    return (len(expression) - 1, False)


class ExpressionValidator:
    """Validates Ignition expression language strings."""

    def validate_expression(
        self,
        expression: str,
        context: str,
        file_path: str,
        component_path: str,
        component_type: str,
    ) -> list[LintIssue]:
        """Validate an Ignition expression and return any issues found."""
        if not expression or not expression.strip():
            return []

        issues: list[LintIssue] = []
        issues.extend(
            self._check_now_polling(
                expression, file_path, component_path, component_type
            )
        )
        issues.extend(
            self._check_property_references(
                expression, file_path, component_path, component_type
            )
        )
        issues.extend(
            self._check_function_names(
                expression, file_path, component_path, component_type
            )
        )
        issues.extend(
            self._check_bad_component_refs(
                expression, file_path, component_path, component_type
            )
        )
        issues.extend(
            self._check_external_index_access(
                expression, file_path, component_path, component_type
            )
        )
        issues.extend(
            self._check_short_circuit_guard(
                expression, file_path, component_path, component_type
            )
        )
        issues.extend(
            self._check_unmatched_parens(
                expression, file_path, component_path, component_type
            )
        )
        issues.extend(
            self._check_unmatched_braces(
                expression, file_path, component_path, component_type
            )
        )
        issues.extend(
            self._check_unmatched_string_quotes(
                expression, file_path, component_path, component_type
            )
        )
        issues.extend(
            self._check_adjacent_expressions(
                expression, file_path, component_path, component_type
            )
        )
        return issues

    def _check_now_polling(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        issues: list[LintIssue] = []

        # now() with no args - defaults to 1000ms polling
        for _m in re.finditer(r"\bnow\s*\(\s*\)", expression):
            issues.append(
                LintIssue(
                    severity=LintSeverity.WARNING,
                    code="EXPR_NOW_DEFAULT_POLLING",
                    message="now() without arguments defaults to 1000ms polling; specify an explicit rate",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component_type,
                    suggestion="Use now(5000) or now(0) for event-driven updates",
                )
            )

        # now(N) with low rate
        for m in re.finditer(r"\bnow\s*\(\s*(\d+)\s*\)", expression):
            rate = int(m.group(1))
            if 0 < rate < 5000:
                issues.append(
                    LintIssue(
                        severity=LintSeverity.INFO,
                        code="EXPR_NOW_LOW_POLLING",
                        message=f"now({rate}) polls at {rate}ms - consider a higher interval for performance",
                        file_path=file_path,
                        component_path=component_path,
                        component_type=component_type,
                        suggestion="Rates below 5000ms can impact client performance",
                    )
                )

        return issues

    def _check_property_references(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        issues: list[LintIssue] = []

        for m in _PROPERTY_REF_RE.finditer(expression):
            ref = m.group(1).strip()
            # Skip tag paths ([Provider]Path), absolute component paths (/root/...),
            # and relative component paths (.../Component Name/...)
            if ref.startswith("[") or ref.startswith("/") or ref.startswith(".."):
                continue
            # {root.custom.X} or {root.params.X} in expressions is invalid — the
            # correct syntax is {view.custom.X} or {view.params.X}.
            if ref.startswith("root.custom.") or ref.startswith("root.params."):
                suffix = ref[len("root.") :]
                issues.append(
                    LintIssue(
                        severity=LintSeverity.ERROR,
                        code="EXPR_ROOT_PROPERTY_REF",
                        message=f"Expression reference '{{{ref}}}' uses root. prefix which is not a valid scope",
                        file_path=file_path,
                        component_path=component_path,
                        component_type=component_type,
                        suggestion=(
                            f"Change to '{{view.{suffix}}}'. "
                            f"Valid scopes are: view, this, session, page"
                        ),
                    )
                )
                continue
            # Flag property refs that contain spaces (likely malformed)
            if " " in ref:
                issues.append(
                    LintIssue(
                        severity=LintSeverity.ERROR,
                        code="EXPR_INVALID_PROPERTY_REF",
                        message=f"Property reference '{{{ref}}}' contains spaces",
                        file_path=file_path,
                        component_path=component_path,
                        component_type=component_type,
                        suggestion="Remove spaces from property reference path",
                    )
                )

        return issues

    def _check_function_names(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        issues: list[LintIssue] = []

        for m in _FUNCTION_CALL_RE.finditer(expression):
            func_name = m.group(1)
            if func_name in _BAD_COMPONENT_REF_FUNCS:
                continue
            # Skip PascalCase names — likely component types, not expression functions
            if func_name[0].isupper():
                continue
            if func_name not in KNOWN_EXPRESSION_FUNCTIONS:
                issues.append(
                    LintIssue(
                        severity=LintSeverity.WARNING,
                        code="EXPR_UNKNOWN_FUNCTION",
                        message=f"Unrecognized expression function '{func_name}'",
                        file_path=file_path,
                        component_path=component_path,
                        component_type=component_type,
                        suggestion="Check Ignition docs for valid expression functions",
                    )
                )

        return issues

    def _check_bad_component_refs(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        issues: list[LintIssue] = []

        for func in _BAD_COMPONENT_REF_FUNCS:
            if re.search(rf"\b{func}\s*\(", expression):
                issues.append(
                    LintIssue(
                        severity=LintSeverity.WARNING,
                        code="EXPR_BAD_COMPONENT_REF",
                        message=f"Component tree traversal '{func}()' in expression is fragile",
                        file_path=file_path,
                        component_path=component_path,
                        component_type=component_type,
                        suggestion="Use view custom properties or message handlers instead",
                    )
                )

        return issues

    def _check_external_index_access(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        """Detect array/dot access outside braces: {X}[n] or {X}[n].prop is invalid."""
        issues: list[LintIssue] = []

        for m in _EXTERNAL_INDEX_RE.finditer(expression):
            prop = m.group(1).strip()
            issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="EXPR_EXTERNAL_INDEX_ACCESS",
                    message=(
                        f"Array index access outside braces on '{{{prop}}}' is invalid syntax"
                    ),
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component_type,
                    suggestion=(
                        f"Move the index inside the braces, e.g. '{{{prop}[0]}}'"
                    ),
                )
            )

        return issues

    def _check_short_circuit_guard(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        """Detect guard-pattern anti-pattern: len(X) && X[n] won't short-circuit."""
        issues: list[LintIssue] = []

        # Only relevant when && or || is present
        if "&&" not in expression and "||" not in expression:
            return issues

        # Collect base property paths that are array-indexed.
        # Handles both external {X}[n] and internal {X[n].prop} forms.
        indexed_props: set[str] = set()
        for m in _EXTERNAL_INDEX_RE.finditer(expression):
            indexed_props.add(m.group(1).strip())
        for m in _INTERNAL_INDEX_RE.finditer(expression):
            indexed_props.add(m.group(1).strip())

        if not indexed_props:
            return issues

        # Check if any size-guard function wraps one of the same property refs
        already_reported: set[str] = set()
        for func in _SIZE_GUARD_FUNCS:
            for m in re.finditer(rf"\b{func}\s*\(\s*\{{([^}}]+)\}}\s*\)", expression):
                guarded_prop = m.group(1).strip()
                if (
                    guarded_prop in indexed_props
                    and guarded_prop not in already_reported
                ):
                    already_reported.add(guarded_prop)
                    op = "&&" if "&&" in expression else "||"
                    issues.append(
                        LintIssue(
                            severity=LintSeverity.WARNING,
                            code="EXPR_NO_SHORT_CIRCUIT",
                            message=(
                                f"'{op}' does not short-circuit in Ignition expressions; "
                                f"{func}({{{guarded_prop}}}) guard will not protect "
                                f"index access on '{{{guarded_prop}}}'"
                            ),
                            file_path=file_path,
                            component_path=component_path,
                            component_type=component_type,
                            suggestion="Use nested if() calls to guard array index access",
                        )
                    )

        return issues

    def _check_unmatched_parens(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        """Detect unmatched parentheses, skipping string literals and {…} blocks."""
        issues: list[LintIssue] = []
        depth = 0
        i = 0
        last_open = -1
        last_extra_close = -1
        while i < len(expression):
            ch = expression[i]
            if ch == "'":
                end, _closed = _skip_string(expression, i)
                i = end + 1
                continue
            if ch == "{":
                # Skip brace block — tag paths may contain parens
                brace_depth = 1
                i += 1
                while i < len(expression) and brace_depth > 0:
                    if expression[i] == "{":
                        brace_depth += 1
                    elif expression[i] == "}":
                        brace_depth -= 1
                    i += 1
                continue
            if ch == "(":
                depth += 1
                last_open = i
            elif ch == ")":
                depth -= 1
                if depth < 0 and last_extra_close < 0:
                    last_extra_close = i
            i += 1

        if depth != 0:
            if depth > 0:
                msg = f"Unmatched opening parenthesis ({depth} unclosed)"
                suggestion = "Add missing closing ')'"
                col = last_open + 1  # 1-indexed
            else:
                msg = f"Unmatched closing parenthesis ({-depth} extra)"
                suggestion = "Remove extra ')' or add matching '('"
                col = (last_extra_close + 1) if last_extra_close >= 0 else 1
            issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="EXPR_UNMATCHED_PAREN",
                    message=msg,
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component_type,
                    suggestion=suggestion,
                    column=col,
                )
            )
        return issues

    def _check_unmatched_braces(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        """Detect unmatched curly braces, skipping string literals."""
        issues: list[LintIssue] = []
        depth = 0
        i = 0
        last_open = -1
        last_extra_close = -1
        while i < len(expression):
            ch = expression[i]
            if ch == "'":
                end, _closed = _skip_string(expression, i)
                i = end + 1
                continue
            if ch == "{":
                depth += 1
                last_open = i
            elif ch == "}":
                depth -= 1
                if depth < 0 and last_extra_close < 0:
                    last_extra_close = i
            i += 1

        if depth != 0:
            if depth > 0:
                msg = f"Unmatched opening brace ({depth} unclosed)"
                suggestion = "Add missing closing '}'"
                col = last_open + 1
            else:
                msg = f"Unmatched closing brace ({-depth} extra)"
                suggestion = "Remove extra '}}' or add matching '{{'"
                col = (last_extra_close + 1) if last_extra_close >= 0 else 1
            issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="EXPR_UNMATCHED_BRACE",
                    message=msg,
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component_type,
                    suggestion=suggestion,
                    column=col,
                )
            )
        return issues

    def _check_unmatched_string_quotes(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        """Detect unclosed string literals (single quotes)."""
        issues: list[LintIssue] = []
        i = 0
        while i < len(expression):
            if expression[i] == "'":
                end, closed = _skip_string(expression, i)
                if not closed:
                    issues.append(
                        LintIssue(
                            severity=LintSeverity.ERROR,
                            code="EXPR_UNMATCHED_QUOTE",
                            message="Unclosed string literal",
                            file_path=file_path,
                            component_path=component_path,
                            component_type=component_type,
                            suggestion="Add missing closing single quote",
                            column=i + 1,  # 1-indexed
                        )
                    )
                    break
                i = end + 1
            else:
                i += 1
        return issues

    def _check_adjacent_expressions(
        self, expression: str, file_path: str, component_path: str, component_type: str
    ) -> list[LintIssue]:
        """Detect adjacent value tokens with no operator between them.

        In Ignition expressions all operators are symbolic (+, -, *, /, etc.)
        so two value-producing tokens back-to-back (with only whitespace) is
        always a syntax error.  Value-ending tokens: ``)``, ``}``, closing
        ``'``, last digit of a number.  Value-starting tokens: ``{``, ``'``,
        digit, identifier (function call).
        """
        issues: list[LintIssue] = []
        i = 0
        length = len(expression)
        # Position of the character that ended the last value token, or -1.
        last_value_end = -1

        def _has_operator_between(start: int, end: int) -> bool:
            """Return True if there is a non-whitespace character between *start* and *end*."""
            return expression[start + 1 : end].strip() != ""

        def _flag(desc: str, pos: int) -> None:
            issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="EXPR_ADJACENT_EXPRESSIONS",
                    message=f"Adjacent expressions with no operator: {desc}",
                    file_path=file_path,
                    component_path=component_path,
                    component_type=component_type,
                    suggestion="Add an operator (+, -, *, /, etc.) or comma between expressions",
                    column=pos + 1,  # 1-indexed
                )
            )

        while i < length:
            ch = expression[i]

            # --- String literal (value) ---
            if ch == "'":
                if last_value_end >= 0 and not _has_operator_between(last_value_end, i):
                    _flag("string literal after value", i)
                end, closed = _skip_string(expression, i)
                if closed:
                    last_value_end = end
                    i = end + 1
                else:
                    break  # unclosed string — other check handles it
                continue

            # --- Property / tag reference (value) ---
            if ch == "{":
                if last_value_end >= 0 and not _has_operator_between(last_value_end, i):
                    _flag("property reference after value", i)
                # Skip to matching }
                brace_depth = 1
                j = i + 1
                while j < length and brace_depth > 0:
                    if expression[j] == "{":
                        brace_depth += 1
                    elif expression[j] == "}":
                        brace_depth -= 1
                    j += 1
                last_value_end = j - 1  # closing }
                i = j
                continue

            # --- Closing paren ends a value (func call / grouping) ---
            if ch == ")":
                last_value_end = i
                i += 1
                continue

            # --- Number literal (value) ---
            if ch.isdigit():
                if last_value_end >= 0 and not _has_operator_between(last_value_end, i):
                    _flag("number literal after value", i)
                # Consume the whole number (digits + optional decimal)
                while i < length and (expression[i].isdigit() or expression[i] == "."):
                    i += 1
                # Handle scientific notation (e.g., 1e10, 1E-5)
                if i < length and expression[i] in "eE":
                    i += 1
                    if i < length and expression[i] in "+-":
                        i += 1
                    while i < length and expression[i].isdigit():
                        i += 1
                last_value_end = i - 1
                continue

            # --- Identifier / function call (value) ---
            if ch.isalpha() or ch == "_":
                if last_value_end >= 0 and not _has_operator_between(last_value_end, i):
                    # Consume identifier
                    j = i
                    while j < length and (
                        expression[j].isalnum() or expression[j] == "_"
                    ):
                        j += 1
                    ident = expression[i:j]
                    _flag(f"'{ident}' after value", i)
                    # Don't update last_value_end — let the normal flow handle it
                # Consume identifier regardless
                while i < length and (expression[i].isalnum() or expression[i] == "_"):
                    i += 1
                # Check if it's a function call — if so, skip into the parens
                # and let ')' handling set last_value_end
                j = i
                while j < length and expression[j] in " \t":
                    j += 1
                if j < length and expression[j] == "(":
                    # It's a function call — don't set last_value_end here;
                    # the matching ')' will set it
                    i = j + 1
                    continue
                # Bare identifier (rare in expressions) — treat as value
                last_value_end = i - 1
                continue

            # --- Operators, commas, whitespace, open parens — reset value tracking ---
            if ch in "+-*/%<>=!&|^~,":
                last_value_end = -1
            elif ch == "(":
                # Opening paren for grouping — not a value end
                last_value_end = -1

            i += 1

        return issues

"""Tests for the ExpressionValidator."""

import pytest

from ignition_lint.validators.expression import ExpressionValidator


@pytest.fixture
def validator():
    return ExpressionValidator()


def _codes(issues):
    return {i.code for i in issues}


class TestNowPolling:
    def test_now_no_args_warns(self, validator):
        issues = validator.validate_expression(
            "now()", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_NOW_DEFAULT_POLLING" in _codes(issues)

    def test_now_low_rate_info(self, validator):
        issues = validator.validate_expression(
            "now(1000)", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_NOW_LOW_POLLING" in _codes(issues)

    def test_now_high_rate_ok(self, validator):
        issues = validator.validate_expression(
            "now(10000)", "test", "file.json", "root", "ia.display.label"
        )
        codes = _codes(issues)
        assert "EXPR_NOW_DEFAULT_POLLING" not in codes
        assert "EXPR_NOW_LOW_POLLING" not in codes

    def test_now_zero_rate_ok(self, validator):
        issues = validator.validate_expression(
            "now(0)", "test", "file.json", "root", "ia.display.label"
        )
        codes = _codes(issues)
        assert "EXPR_NOW_DEFAULT_POLLING" not in codes
        assert "EXPR_NOW_LOW_POLLING" not in codes


class TestBadComponentRefs:
    def test_get_sibling_flagged(self, validator):
        issues = validator.validate_expression(
            "getSibling(0, 'Label')", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_BAD_COMPONENT_REF" in _codes(issues)

    def test_normal_function_passes(self, validator):
        issues = validator.validate_expression(
            "toStr(42)", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_BAD_COMPONENT_REF" not in _codes(issues)

    def test_get_parent_flagged(self, validator):
        issues = validator.validate_expression(
            "getParent().custom.value", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_BAD_COMPONENT_REF" in _codes(issues)


class TestPropertyReferences:
    def test_spaces_flagged(self, validator):
        issues = validator.validate_expression(
            "{view.custom. spacedProp}", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_INVALID_PROPERTY_REF" in _codes(issues)

    def test_valid_ref_passes(self, validator):
        issues = validator.validate_expression(
            "{view.custom.myProp}", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_INVALID_PROPERTY_REF" not in _codes(issues)


class TestFunctionNames:
    def test_known_function_ok(self, validator):
        issues = validator.validate_expression(
            "toStr(42) + dateFormat(now(5000), 'HH:mm')",
            "test",
            "file.json",
            "root",
            "ia.display.label",
        )
        assert "EXPR_UNKNOWN_FUNCTION" not in _codes(issues)

    def test_unknown_function_flagged(self, validator):
        issues = validator.validate_expression(
            "fooBarBaz(42)", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNKNOWN_FUNCTION" in _codes(issues)


class TestRootPropertyRef:
    def test_root_custom_flagged(self, validator):
        """Expression {root.custom.X} should be {view.custom.X}."""
        issues = validator.validate_expression(
            "{root.custom.auditData}",
            "test",
            "file.json",
            "root",
            "ia.display.table",
        )
        assert "EXPR_ROOT_PROPERTY_REF" in _codes(issues)
        issue = next(i for i in issues if i.code == "EXPR_ROOT_PROPERTY_REF")
        assert "{view.custom.auditData}" in issue.suggestion
        assert "view, this, session, page" in issue.suggestion

    def test_root_params_flagged(self, validator):
        """Expression {root.params.X} should be {view.params.X}."""
        issues = validator.validate_expression(
            "{root.params.item}",
            "test",
            "file.json",
            "root",
            "ia.display.label",
        )
        assert "EXPR_ROOT_PROPERTY_REF" in _codes(issues)

    def test_view_custom_ok(self, validator):
        """Correct {view.custom.X} should not be flagged."""
        issues = validator.validate_expression(
            "{view.custom.auditData}",
            "test",
            "file.json",
            "root",
            "ia.display.table",
        )
        assert "EXPR_ROOT_PROPERTY_REF" not in _codes(issues)

    def test_this_custom_ok(self, validator):
        """Correct {this.custom.X} should not be flagged."""
        issues = validator.validate_expression(
            "{this.custom.mode}",
            "test",
            "file.json",
            "root",
            "ia.display.label",
        )
        assert "EXPR_ROOT_PROPERTY_REF" not in _codes(issues)


class TestExternalIndexAccess:
    def test_index_outside_braces_flagged(self, validator):
        """{X}[1] is invalid — index must be inside braces."""
        expr = "{view.params.steps}[1].complete"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_EXTERNAL_INDEX_ACCESS" in _codes(issues)
        issue = next(i for i in issues if i.code == "EXPR_EXTERNAL_INDEX_ACCESS")
        assert issue.severity.name == "ERROR"
        assert "{view.params.steps[0]}" in issue.suggestion

    def test_index_outside_braces_in_if(self, validator):
        """Full if() expression with external index is flagged."""
        expr = (
            "if(len({view.params.steps}) > 1 && {view.params.steps}[1].complete, "
            "'complete', 'pending')"
        )
        issues = validator.validate_expression(
            expr, "test", "file.json", "root/Connector01", "ia.display.label"
        )
        assert "EXPR_EXTERNAL_INDEX_ACCESS" in _codes(issues)

    def test_index_inside_braces_ok(self, validator):
        """Correct syntax {X[1].complete} should not flag."""
        expr = "{view.params.steps[1].complete}"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_EXTERNAL_INDEX_ACCESS" not in _codes(issues)

    def test_no_index_no_flag(self, validator):
        """Simple property ref without indexing should not flag."""
        expr = "{view.params.steps}"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_EXTERNAL_INDEX_ACCESS" not in _codes(issues)


class TestNoShortCircuit:
    def test_len_guard_with_and_external_index(self, validator):
        """len(X) > N && X[N] (external) should warn for both rules."""
        expr = (
            "if(len({view.params.steps}) > 1 && {view.params.steps}[1].complete, "
            "'complete', 'pending')"
        )
        issues = validator.validate_expression(
            expr, "test", "file.json", "root/Connector01", "ia.display.label"
        )
        codes = _codes(issues)
        assert "EXPR_NO_SHORT_CIRCUIT" in codes
        assert "EXPR_EXTERNAL_INDEX_ACCESS" in codes

    def test_len_guard_with_and_internal_index(self, validator):
        """len(X) > N && {X[N].prop} (correct syntax) still has short-circuit issue."""
        expr = (
            "if(len({view.params.steps}) > 1 && {view.params.steps[1].complete}, "
            "'complete', 'pending')"
        )
        issues = validator.validate_expression(
            expr, "test", "file.json", "root/Connector01", "ia.display.label"
        )
        codes = _codes(issues)
        assert "EXPR_NO_SHORT_CIRCUIT" in codes
        assert "EXPR_EXTERNAL_INDEX_ACCESS" not in codes
        issue = next(i for i in issues if i.code == "EXPR_NO_SHORT_CIRCUIT")
        assert "nested if()" in issue.suggestion

    def test_len_guard_with_or_flagged(self, validator):
        """len(X) == 0 || {X[0]} should warn — || doesn't short-circuit."""
        expr = "if(len({view.params.items}) == 0 || {view.params.items[0].disabled}, 'off', 'on')"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_NO_SHORT_CIRCUIT" in _codes(issues)

    def test_json_length_guard_flagged(self, validator):
        """jsonLength() guard + array index should also flag."""
        expr = "if(jsonLength({this.custom.data}) > 0 && {this.custom.data[0]}, 'yes', 'no')"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_NO_SHORT_CIRCUIT" in _codes(issues)

    def test_no_guard_no_flag(self, validator):
        """Array indexing without a length guard should not flag short-circuit."""
        expr = "if({view.params.steps[0].complete}, 'done', 'pending')"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_NO_SHORT_CIRCUIT" not in _codes(issues)

    def test_and_without_array_index_no_flag(self, validator):
        """&& without array indexing should not flag."""
        expr = "if({view.params.a} > 0 && {view.params.b} > 0, 'yes', 'no')"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_NO_SHORT_CIRCUIT" not in _codes(issues)

    def test_nested_if_no_flag(self, validator):
        """Properly nested if() with separate guard should not flag."""
        expr = (
            "if(len({view.params.steps}) > 1, "
            "if({view.params.steps[1].complete}, 'complete', 'pending'), "
            "'pending')"
        )
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_NO_SHORT_CIRCUIT" not in _codes(issues)


class TestUnmatchedParens:
    def test_missing_close_paren(self, validator):
        issues = validator.validate_expression(
            "runScript('test', 1000", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_PAREN" in _codes(issues)

    def test_extra_close_paren(self, validator):
        issues = validator.validate_expression(
            "toStr(42))", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_PAREN" in _codes(issues)

    def test_balanced_parens(self, validator):
        issues = validator.validate_expression(
            "if(toStr(42) = '42', 'yes', 'no')",
            "test",
            "file.json",
            "root",
            "ia.display.label",
        )
        assert "EXPR_UNMATCHED_PAREN" not in _codes(issues)

    def test_parens_inside_string_ignored(self, validator):
        """Parens inside string literals should not be counted."""
        issues = validator.validate_expression(
            "toStr('(hello)')", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_PAREN" not in _codes(issues)

    def test_parens_inside_tag_ref_ignored(self, validator):
        """Parens inside {…} tag refs should not be counted."""
        issues = validator.validate_expression(
            "toStr({[default]Tag (1)/Value})",
            "test",
            "file.json",
            "root",
            "ia.display.label",
        )
        assert "EXPR_UNMATCHED_PAREN" not in _codes(issues)

    def test_no_parens_ok(self, validator):
        issues = validator.validate_expression(
            "{view.custom.value}", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_PAREN" not in _codes(issues)


class TestUnmatchedBraces:
    def test_missing_close_brace(self, validator):
        issues = validator.validate_expression(
            "{[default]Tag * 2", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_BRACE" in _codes(issues)

    def test_extra_close_brace(self, validator):
        issues = validator.validate_expression(
            "{view.custom.x}} + 1", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_BRACE" in _codes(issues)

    def test_balanced_braces(self, validator):
        issues = validator.validate_expression(
            "{view.custom.a} + {view.custom.b}",
            "test",
            "file.json",
            "root",
            "ia.display.label",
        )
        assert "EXPR_UNMATCHED_BRACE" not in _codes(issues)

    def test_braces_inside_string_ignored(self, validator):
        """Braces inside string literals should not be counted."""
        issues = validator.validate_expression(
            "toStr('{hello}')", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_BRACE" not in _codes(issues)

    def test_no_braces_ok(self, validator):
        issues = validator.validate_expression(
            "toStr(42)", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_BRACE" not in _codes(issues)


class TestUnmatchedQuotes:
    def test_unclosed_string(self, validator):
        issues = validator.validate_expression(
            "runScript('test, 1000)", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_QUOTE" in _codes(issues)

    def test_balanced_strings(self, validator):
        issues = validator.validate_expression(
            "if(1, 'yes', 'no')", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_QUOTE" not in _codes(issues)

    def test_empty_string_ok(self, validator):
        issues = validator.validate_expression(
            "toStr('')", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_QUOTE" not in _codes(issues)

    def test_no_quotes_ok(self, validator):
        issues = validator.validate_expression(
            "{view.custom.x} + 1", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNMATCHED_QUOTE" not in _codes(issues)

    def test_multiple_strings_last_unclosed(self, validator):
        issues = validator.validate_expression(
            "if(1, 'yes', 'no)",
            "test",
            "file.json",
            "root",
            "ia.display.label",
        )
        assert "EXPR_UNMATCHED_QUOTE" in _codes(issues)


class TestAdjacentExpressions:
    def test_back_to_back_function_calls(self, validator):
        """runScript()runScript(...) should be flagged."""
        expr = "runScript()runScript('core.proj.func', 1000)"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" in _codes(issues)

    def test_back_to_back_with_space(self, validator):
        """runScript() runScript(...) should also be flagged."""
        expr = "runScript() runScript('core.proj.func', 1000)"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" in _codes(issues)

    def test_ref_then_func_call(self, validator):
        """{view.custom.x} runScript(...) — missing operator."""
        expr = "{view.custom.x} runScript('func', 1000)"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" in _codes(issues)

    def test_ref_then_ref(self, validator):
        """{x}{y} — two adjacent property refs."""
        expr = "{view.custom.x}{view.custom.y}"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" in _codes(issues)

    def test_func_then_number(self, validator):
        """toStr(1) 42 — value then number literal."""
        expr = "toStr(1) 42"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" in _codes(issues)

    def test_func_then_string(self, validator):
        """toStr(1) 'hello' — value then string literal."""
        expr = "toStr(1) 'hello'"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" in _codes(issues)

    def test_func_then_ref(self, validator):
        """toStr(1) {view.custom.x} — value then property ref."""
        expr = "toStr(1) {view.custom.x}"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" in _codes(issues)

    def test_number_then_func(self, validator):
        """42 toStr(1) — number then function call."""
        expr = "42 toStr(1)"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" in _codes(issues)

    def test_string_then_ref(self, validator):
        """'hello' {view.custom.x} — string then ref."""
        expr = "'hello' {view.custom.x}"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" in _codes(issues)

    def test_operator_between_calls_ok(self, validator):
        """toStr(1) + toStr(2) is valid."""
        issues = validator.validate_expression(
            "toStr(1) + toStr(2)", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" not in _codes(issues)

    def test_operator_between_ref_and_number_ok(self, validator):
        """{view.custom.x} * 2 is valid."""
        issues = validator.validate_expression(
            "{view.custom.x} * 2", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" not in _codes(issues)

    def test_comma_separated_ok(self, validator):
        """Function args like if(toStr(1), toStr(2)) are valid."""
        issues = validator.validate_expression(
            "if(toStr(1), toStr(2), toStr(3))",
            "test",
            "file.json",
            "root",
            "ia.display.label",
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" not in _codes(issues)

    def test_nested_function_ok(self, validator):
        """toStr(abs(1)) is valid — ')' followed by ')' not an identifier."""
        issues = validator.validate_expression(
            "toStr(abs(1))", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" not in _codes(issues)

    def test_adjacent_in_string_ignored(self, validator):
        """Text inside strings should not trigger the check."""
        issues = validator.validate_expression(
            "toStr('foo()bar()')", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" not in _codes(issues)

    def test_ref_with_operator_ok(self, validator):
        """{x} + {y} is valid."""
        issues = validator.validate_expression(
            "{view.custom.a} + {view.custom.b}",
            "test",
            "file.json",
            "root",
            "ia.display.label",
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" not in _codes(issues)

    def test_complex_valid_expression(self, validator):
        """Real-world expression with multiple tokens and operators."""
        expr = "if({view.custom.x} > 0, toStr({view.custom.x} * 2), 'none')"
        issues = validator.validate_expression(
            expr, "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_ADJACENT_EXPRESSIONS" not in _codes(issues)

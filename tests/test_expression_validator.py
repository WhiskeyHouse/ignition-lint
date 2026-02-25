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

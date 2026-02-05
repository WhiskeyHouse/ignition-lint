"""Tests for the ExpressionValidator."""
import pytest

from ignition_lint.validators.expression import ExpressionValidator
from ignition_lint.reporting import LintSeverity


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
            "test", "file.json", "root", "ia.display.label",
        )
        assert "EXPR_UNKNOWN_FUNCTION" not in _codes(issues)

    def test_unknown_function_flagged(self, validator):
        issues = validator.validate_expression(
            "fooBarBaz(42)", "test", "file.json", "root", "ia.display.label"
        )
        assert "EXPR_UNKNOWN_FUNCTION" in _codes(issues)

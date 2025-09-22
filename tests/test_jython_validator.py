import pytest

from ignition_lint.validators.jython import JythonValidator
from ignition_lint.reporting import LintSeverity


def validate(script: str):
    validator = JythonValidator()
    return validator.validate_script(script, context="test")


def test_detects_indentation():
    issues = validate("value = 1\nprint(value)\n")
    codes = {issue.code for issue in issues}
    assert "JYTHON_INDENTATION_REQUIRED" in codes


def test_detects_syntax_error():
    issues = validate("\tif value > 5\n\t\treturn 'high'")
    assert any(issue.severity == LintSeverity.ERROR for issue in issues)


def test_detects_best_practices():
    issues = validate("\turl = 'http://localhost'\n\tresponse = system.net.httpClient().post(url)")
    codes = {issue.code for issue in issues}
    assert "JYTHON_HARDCODED_LOCALHOST" in codes
    assert "JYTHON_HTTP_WITHOUT_EXCEPTION_HANDLING" in codes


def test_clean_script_produces_no_issues():
    script = "\ttry:\n\t\treturn system.date.now()\n\texcept Exception as err:\n\t\tsystem.perspective.print(str(err))"
    assert validate(script) == []

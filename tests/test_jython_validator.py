from ignition_lint.reporting import LintSeverity
from ignition_lint.validators.jython import JythonValidator


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
    issues = validate(
        "\turl = 'http://localhost'\n\tresponse = system.net.httpClient().post(url)"
    )
    codes = {issue.code for issue in issues}
    assert "JYTHON_HARDCODED_LOCALHOST" in codes
    assert "JYTHON_HTTP_WITHOUT_EXCEPTION_HANDLING" in codes


def test_clean_script_produces_no_issues():
    script = "\ttry:\n\t\treturn system.date.now()\n\texcept Exception as err:\n\t\tsystem.perspective.print(str(err))"
    assert validate(script) == []


class TestPy2Preprocessing:
    """Ensure Python 2 constructs don't cause spurious JYTHON_SYNTAX_ERROR."""

    def test_print_statement_no_syntax_error(self):
        script = '\tprint "hello world"'
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes
        assert "JYTHON_PRINT_STATEMENT" in codes

    def test_print_variable_no_syntax_error(self):
        script = "\tprint value"
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes
        assert "JYTHON_PRINT_STATEMENT" in codes

    def test_print_multiple_args_no_syntax_error(self):
        script = '\tprint "x =", x, "y =", y'
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes

    def test_print_redirect_no_syntax_error(self):
        script = "\tprint >>sys.stderr, 'error'"
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes

    def test_except_comma_syntax_no_error(self):
        script = "\ttry:\n\t\tpass\n\texcept Exception, e:\n\t\tpass"
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes

    def test_raise_comma_syntax_no_error(self):
        script = '\traise ValueError, "bad value"'
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes

    def test_genuine_syntax_error_still_caught(self):
        script = "\tif x >\n\t\tpass"
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" in codes

    def test_print_function_call_unchanged(self):
        """print(x) should not be mangled by preprocessing."""
        script = "\tprint(42)"
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes


class TestTripleQuotedStrings:
    """Lines inside triple-quoted strings must not trigger indentation errors."""

    def test_triple_double_quoted_graphql(self):
        """GraphQL inside triple double-quotes should not trigger indentation."""
        script = (
            '\tquery = """\n{\n  users {\n    id\n    name\n  }\n}\n"""\n\treturn query'
        )
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_INDENTATION_REQUIRED" not in codes
        assert "JYTHON_INCONSISTENT_INDENTATION_STYLE" not in codes

    def test_triple_single_quoted_sql(self):
        """SQL inside triple single-quotes should not trigger indentation."""
        script = (
            "\tsql = '''\n"
            "SELECT id, name\n"
            "FROM users\n"
            "WHERE active = 1\n"
            "'''\n"
            "\treturn sql"
        )
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_INDENTATION_REQUIRED" not in codes

    def test_real_indentation_error_outside_triple_quote(self):
        """Indentation errors outside triple-quoted strings are still caught."""
        script = (
            '\tquery = """\n'
            "SELECT *\n"
            '"""\n'
            "bad_line = 1\n"  # no indentation — should be flagged
        )
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_INDENTATION_REQUIRED" in codes

    def test_triple_quote_open_and_close_same_line(self):
        """Triple-quote open+close on same line doesn't corrupt state."""
        script = '\tx = """inline string"""\n\ty = 1'
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_INDENTATION_REQUIRED" not in codes

    def test_multiple_triple_quoted_blocks(self):
        """Multiple triple-quoted blocks should all be skipped."""
        script = (
            '\tq1 = """\nSELECT 1\n"""\n'
            "\tq2 = '''\nSELECT 2\n'''\n"
            "\treturn q1 + q2"
        )
        issues = validate(script)
        codes = {i.code for i in issues}
        assert "JYTHON_INDENTATION_REQUIRED" not in codes


def validate_with_context(script: str, context: str):
    validator = JythonValidator()
    return validator.validate_script(script, context=context)


class TestStandaloneMode:
    """standalone=True skips indentation but keeps other checks."""

    def test_standalone_skips_indentation_check(self):
        """standalone=True suppresses indentation diagnostics."""
        v = JythonValidator()
        # Script with no leading indent — would normally trigger JYTHON_INDENTATION_REQUIRED
        issues = v.validate_script(
            "from core import x\nreturn x", context="script", standalone=True
        )
        codes = [i.code for i in issues]
        assert "JYTHON_INDENTATION_REQUIRED" not in codes
        assert "JYTHON_INCONSISTENT_INDENTATION_STYLE" not in codes

    def test_standalone_still_checks_syntax(self):
        """standalone=True still validates Python syntax."""
        v = JythonValidator()
        issues = v.validate_script("def foo(\n", context="script", standalone=True)
        codes = [i.code for i in issues]
        assert "JYTHON_SYNTAX_ERROR" in codes

    def test_standalone_transform_no_false_syntax_error(self):
        """standalone=True with a transform context should not produce a false syntax error."""
        v = JythonValidator()
        # Dedented transform body — no leading tabs
        issues = v.validate_script(
            "if value > 10:\n    return 'high'\nreturn 'low'",
            context="transform[0]",
            standalone=True,
        )
        codes = [i.code for i in issues]
        assert "JYTHON_SYNTAX_ERROR" not in codes

    def test_standalone_still_checks_patterns(self):
        """standalone=True still runs ignition pattern checks."""
        v = JythonValidator()
        issues = v.validate_script(
            "print('hello')\n", context="script", standalone=True
        )
        codes = [i.code for i in issues]
        assert "JYTHON_PREFER_PERSPECTIVE_PRINT" in codes


class TestTransformSyntax:
    """Transform scripts should be parsed correctly despite leading indentation."""

    def test_transform_with_triple_quoted_string(self):
        """Transform containing triple-quoted string should not produce syntax error."""
        script = '\tquery = """\n{\n  users {\n    id\n  }\n"""\n\treturn query'
        issues = validate_with_context(script, "transform[0]")
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes

    def test_transform_genuine_syntax_error(self):
        """Genuine syntax errors in transforms are still caught."""
        script = "\tif value >\n\t\tpass"
        issues = validate_with_context(script, "transform[0]")
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" in codes

    def test_simple_transform_parses(self):
        """Simple transform scripts parse without issue."""
        script = "\tif value > 10:\n\t\treturn 'high'\n\treturn 'low'"
        issues = validate_with_context(script, "transform[0]")
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes

    def test_binding_transform_context_variant(self):
        """Context like 'view.binding.transform[0]' should also trigger wrapping."""
        script = "\treturn str(value)"
        issues = validate_with_context(script, "view.binding.transform[0]")
        codes = {i.code for i in issues}
        assert "JYTHON_SYNTAX_ERROR" not in codes

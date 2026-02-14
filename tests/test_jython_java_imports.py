"""Tests for Java import validation in JythonValidator."""

from ignition_lint.validators.jython import JythonValidator


def validate(script: str):
    validator = JythonValidator()
    return validator.validate_script(script, context="test.py")


def codes(issues):
    return {issue.code for issue in issues}


class TestKnownJavaPackage:
    """Known Java packages should not trigger JYTHON_UNKNOWN_JAVA_PACKAGE."""

    def test_java_lang_not_flagged(self):
        script = "from java.lang import String\nx = String.valueOf(42)"
        assert "JYTHON_UNKNOWN_JAVA_PACKAGE" not in codes(validate(script))

    def test_java_util_not_flagged(self):
        script = "from java.util import ArrayList\nlst = ArrayList()"
        assert "JYTHON_UNKNOWN_JAVA_PACKAGE" not in codes(validate(script))

    def test_java_net_not_flagged(self):
        script = "from java.net import URL\nu = URL('http://example.com')"
        assert "JYTHON_UNKNOWN_JAVA_PACKAGE" not in codes(validate(script))

    def test_ignition_common_not_flagged(self):
        script = "from com.inductiveautomation.ignition.common import Dataset\nds = Dataset()"
        assert "JYTHON_UNKNOWN_JAVA_PACKAGE" not in codes(validate(script))


class TestUnknownJavaPackage:
    """Unknown Java-like packages should trigger JYTHON_UNKNOWN_JAVA_PACKAGE."""

    def test_unknown_java_package_flagged(self):
        script = "from java.foo import Bar\nx = Bar()"
        issues = validate(script)
        assert "JYTHON_UNKNOWN_JAVA_PACKAGE" in codes(issues)

    def test_unknown_javax_package_flagged(self):
        script = "from javax.fake import Widget\nw = Widget()"
        issues = validate(script)
        assert "JYTHON_UNKNOWN_JAVA_PACKAGE" in codes(issues)

    def test_unknown_ignition_package_flagged(self):
        script = "from com.inductiveautomation.fake import Stuff\ns = Stuff()"
        issues = validate(script)
        assert "JYTHON_UNKNOWN_JAVA_PACKAGE" in codes(issues)

    def test_non_java_import_not_flagged(self):
        """Regular Python imports should not be flagged."""
        script = "from collections import OrderedDict\nd = OrderedDict()"
        assert "JYTHON_UNKNOWN_JAVA_PACKAGE" not in codes(validate(script))

    def test_system_import_not_flagged(self):
        """system.* imports are not Java packages."""
        script = "import system\nv = system.tag.readBlocking(['tag'])"
        assert "JYTHON_UNKNOWN_JAVA_PACKAGE" not in codes(validate(script))


class TestWildcardImport:
    """Wildcard Java imports should trigger JYTHON_IMPORT_STAR."""

    def test_wildcard_import_flagged(self):
        script = "from java.util import *\nlst = ArrayList()"
        issues = validate(script)
        assert "JYTHON_IMPORT_STAR" in codes(issues)

    def test_wildcard_javax_flagged(self):
        script = "from javax.swing import *\nf = JFrame()"
        issues = validate(script)
        assert "JYTHON_IMPORT_STAR" in codes(issues)

    def test_explicit_import_not_flagged_as_star(self):
        script = "from java.util import ArrayList\nlst = ArrayList()"
        assert "JYTHON_IMPORT_STAR" not in codes(validate(script))

    def test_wildcard_non_java_not_flagged(self):
        """Wildcard imports of non-Java packages are not our concern."""
        script = "from os.path import *\np = join('a', 'b')"
        assert "JYTHON_IMPORT_STAR" not in codes(validate(script))


class TestUnusedJavaImport:
    """Unused Java imports should trigger JYTHON_UNUSED_JAVA_IMPORT."""

    def test_unused_import_flagged(self):
        script = "from java.util import ArrayList\nprint('hello')"
        issues = validate(script)
        assert "JYTHON_UNUSED_JAVA_IMPORT" in codes(issues)

    def test_used_import_not_flagged(self):
        script = "from java.util import ArrayList\nlst = ArrayList()"
        assert "JYTHON_UNUSED_JAVA_IMPORT" not in codes(validate(script))

    def test_multiple_imports_partial_unused(self):
        script = "from java.util import ArrayList, HashMap\nlst = ArrayList()"
        issues = validate(script)
        issue_codes = codes(issues)
        assert "JYTHON_UNUSED_JAVA_IMPORT" in issue_codes
        unused = [i for i in issues if i.code == "JYTHON_UNUSED_JAVA_IMPORT"]
        assert len(unused) == 1
        assert "HashMap" in unused[0].message

    def test_aliased_import_used(self):
        script = (
            "from java.lang import Exception as JException\nraise JException('err')"
        )
        assert "JYTHON_UNUSED_JAVA_IMPORT" not in codes(validate(script))

    def test_aliased_import_unused(self):
        script = "from java.lang import Exception as JException\nprint('ok')"
        issues = validate(script)
        unused = [i for i in issues if i.code == "JYTHON_UNUSED_JAVA_IMPORT"]
        assert len(unused) == 1
        assert "JException" in unused[0].message


class TestJavaImportLineNumbers:
    """Java import issues should include correct line numbers."""

    def test_unknown_package_has_line_number(self):
        script = "x = 1\nfrom java.bogus import Thing\ny = Thing()"
        issues = validate(script)
        unknown = [i for i in issues if i.code == "JYTHON_UNKNOWN_JAVA_PACKAGE"]
        assert len(unknown) == 1
        assert unknown[0].line_number == 2

    def test_wildcard_import_has_line_number(self):
        script = "x = 1\ny = 2\nfrom java.util import *\nz = ArrayList()"
        issues = validate(script)
        star = [i for i in issues if i.code == "JYTHON_IMPORT_STAR"]
        assert len(star) == 1
        assert star[0].line_number == 3

    def test_unused_import_has_line_number(self):
        script = "from java.net import URL\nfrom java.util import HashMap\nx = URL('http://x.com')"
        issues = validate(script)
        unused = [i for i in issues if i.code == "JYTHON_UNUSED_JAVA_IMPORT"]
        assert len(unused) == 1
        assert unused[0].line_number == 2

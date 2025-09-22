from ignition_lint.cli import determine_checks


def test_determine_checks_profile_defaults():
    assert determine_checks("default", None, False) == {"perspective", "naming", "scripts"}


def test_determine_checks_naming_only():
    assert determine_checks("default", None, True) == {"naming"}


def test_determine_checks_explicit():
    assert determine_checks("default", "perspective,scripts", False) == {"perspective", "scripts"}

"""Test that malformed tag nodes are properly rejected."""

import json
import os
import tempfile

from ignition_lint.tags.linter import IgnitionTagLinter


def test_malformed_tag_node_rejected():
    """Non-dict tag nodes should be rejected with an error."""
    linter = IgnitionTagLinter()

    # Create a test file with a malformed tag (string instead of dict)
    malformed_data = "not a dict"

    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "malformed.json")

    try:
        with open(path, "w") as f:
            json.dump(malformed_data, f)

        result = linter.lint_file(path)

        # Should return False (invalid)
        assert result is False, "Malformed tag should fail validation"

        # Should have an INVALID_TAG_NODE error
        codes = {issue.code for issue in linter.issues}
        assert "INVALID_TAG_NODE" in codes, "Should report INVALID_TAG_NODE error"

        # Check error message
        invalid_issues = [i for i in linter.issues if i.code == "INVALID_TAG_NODE"]
        assert len(invalid_issues) == 1
        assert "str" in invalid_issues[0].message
        assert "not a dict" in invalid_issues[0].message

    finally:
        os.unlink(path)
        os.rmdir(tmpdir)


def test_malformed_child_tag_rejected():
    """Non-dict child tags should be rejected with an error."""
    linter = IgnitionTagLinter()

    # Parent tag is valid, but child is malformed
    data = {
        "name": "ParentFolder",
        "tagType": "Folder",
        "tags": [
            {
                "name": "ValidChild",
                "tagType": "AtomicTag",
                "dataType": "Int4",
                "valueSource": "memory",
            },
            "malformed string child",  # This should be rejected
            123,  # This should also be rejected
        ],
    }

    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "parent.json")

    try:
        with open(path, "w") as f:
            json.dump(data, f)

        result = linter.lint_file(path)

        # Should return False (invalid due to malformed children)
        assert result is False, "Should fail validation due to malformed children"

        # Should have INVALID_TAG_NODE errors for the two malformed children
        invalid_issues = [i for i in linter.issues if i.code == "INVALID_TAG_NODE"]
        assert len(invalid_issues) == 2, f"Expected 2 errors, got {len(invalid_issues)}"

        # Check that both malformed children are reported
        messages = [i.message for i in invalid_issues]
        assert any("str" in msg for msg in messages), "Should report string child"
        assert any("int" in msg for msg in messages), "Should report int child"

    finally:
        os.unlink(path)
        os.rmdir(tmpdir)


def test_array_with_malformed_entry():
    """Top-level arrays with malformed entries should be rejected."""
    linter = IgnitionTagLinter()

    # Array with one valid and one malformed entry
    data = [
        {
            "name": "ValidTag",
            "tagType": "AtomicTag",
            "dataType": "Int4",
            "valueSource": "memory",
        },
        ["nested", "array"],  # This should be rejected
    ]

    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "array.json")

    try:
        with open(path, "w") as f:
            json.dump(data, f)

        result = linter.lint_file(path)

        # Should return False due to malformed entry
        assert result is False, "Should fail validation due to malformed array entry"

        # Should have INVALID_TAG_NODE error
        invalid_issues = [i for i in linter.issues if i.code == "INVALID_TAG_NODE"]
        assert len(invalid_issues) == 1
        assert "list" in invalid_issues[0].message

    finally:
        os.unlink(path)
        os.rmdir(tmpdir)


if __name__ == "__main__":
    test_malformed_tag_node_rejected()
    print("✓ test_malformed_tag_node_rejected passed")

    test_malformed_child_tag_rejected()
    print("✓ test_malformed_child_tag_rejected passed")

    test_array_with_malformed_entry()
    print("✓ test_array_with_malformed_entry passed")

    print("\nAll tests passed!")

#!/usr/bin/env python3
"""
Language Server Protocol adapter for Ignition Perspective Linter
Enables real-time linting in VS Code and other LSP-compatible editors
"""

import json
import sys
from typing import Any

from ignition_lint.perspective.linter import IgnitionPerspectiveLinter


class IgnitionLSPServer:
    def __init__(self):
        self.linter = IgnitionPerspectiveLinter()

    def lint_document(self, file_path: str, content: str) -> list[dict[str, Any]]:
        """Convert linter issues to LSP diagnostics format"""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            severity_map = {
                "error": 1,  # LSP Error
                "warning": 2,  # LSP Warning
                "info": 3,  # LSP Information
                "style": 4,  # LSP Hint
            }

            # lint_file returns bool; issues accumulate in self.linter.issues
            self.linter.issues.clear()
            success = self.linter.lint_file(temp_path)
            diagnostics = []

            if not success:
                return diagnostics

            for issue in self.linter.issues:
                line = (issue.line_number if issue.line_number is not None else 1) - 1
                diagnostic = {
                    "range": {
                        "start": {"line": line, "character": 0},
                        "end": {"line": line, "character": 100},
                    },
                    "severity": severity_map.get(issue.severity.value, 2),
                    "message": issue.message,
                    "source": "ignition-perspective-linter",
                    "code": issue.code or "unknown",
                }
                diagnostics.append(diagnostic)

            return diagnostics

        except Exception as e:
            return [
                {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 100},
                    },
                    "severity": 1,
                    "message": f"Linting error: {str(e)}",
                    "source": "ignition-perspective-linter",
                }
            ]
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


def main():
    """Simple stdio-based LSP server for agent integration"""
    server = IgnitionLSPServer()

    for line in sys.stdin:
        request = None
        try:
            request = json.loads(line.strip())

            if request.get("method") == "lint":
                file_path = request["params"]["uri"]
                content = request["params"]["text"]
                diagnostics = server.lint_document(file_path, content)

                response = {
                    "id": request.get("id"),
                    "result": {"diagnostics": diagnostics},
                }
                print(json.dumps(response))

        except Exception as e:
            error_response = {
                "id": (request or {}).get("id"),
                "error": {"code": -1, "message": str(e)},
            }
            print(json.dumps(error_response))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Language Server Protocol adapter for Ignition Perspective Linter
Enables real-time linting in VS Code and other LSP-compatible editors
"""

import json
import sys
from typing import Dict, List, Any
from ignition_perspective_linter import IgnitionPerspectiveLinter

class IgnitionLSPServer:
    def __init__(self):
        self.linter = IgnitionPerspectiveLinter()
        
    def lint_document(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Convert linter issues to LSP diagnostics format"""
        try:
            # Save content to temp file for linting
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            results = self.linter.lint_file(temp_path)
            diagnostics = []
            
            for issue in results.get("issues", {}).get(temp_path, []):
                severity_map = {
                    "error": 1,    # LSP Error
                    "warning": 2,  # LSP Warning  
                    "info": 3,     # LSP Information
                    "style": 4     # LSP Hint
                }
                
                diagnostic = {
                    "range": {
                        "start": {"line": issue.get("line", 0), "character": 0},
                        "end": {"line": issue.get("line", 0), "character": 100}
                    },
                    "severity": severity_map.get(issue["severity"], 2),
                    "message": issue["message"],
                    "source": "ignition-perspective-linter",
                    "code": issue.get("rule", "unknown")
                }
                diagnostics.append(diagnostic)
            
            # Cleanup
            import os
            os.unlink(temp_path)
            
            return diagnostics
            
        except Exception as e:
            return [{
                "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 100}},
                "severity": 1,
                "message": f"Linting error: {str(e)}",
                "source": "ignition-perspective-linter"
            }]

def main():
    """Simple stdio-based LSP server for agent integration"""
    server = IgnitionLSPServer()
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            
            if request.get("method") == "lint":
                file_path = request["params"]["uri"]
                content = request["params"]["text"]
                diagnostics = server.lint_document(file_path, content)
                
                response = {
                    "id": request.get("id"),
                    "result": {"diagnostics": diagnostics}
                }
                print(json.dumps(response))
                
        except Exception as e:
            error_response = {
                "id": request.get("id", None),
                "error": {"code": -1, "message": str(e)}
            }
            print(json.dumps(error_response))

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
FastMCP Server for Ignition Empirical Linter Integration
Provides Model Context Protocol interface to the empirical ignition linter.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# FastMCP imports
try:
    from fastmcp import FastMCP
except ImportError:
    print("❌ FastMCP library not found. Install with: pip install fastmcp")
    sys.exit(1)

# Path to our linter script and empirical linter
PROJECT_ROOT = Path(__file__).parent
LINT_SCRIPT = PROJECT_ROOT / "cli.py"
EMPIRICAL_LINTER_PATH = (
    PROJECT_ROOT.parent.parent.parent
    / "empirical-ignition-perspective-component-schema"
)

# Initialize FastMCP server
mcp = FastMCP("Ignition Empirical Linter")


@mcp.resource("ignition://linter/status")
def get_linter_status() -> str:
    """Check if empirical ignition linter is available."""
    try:
        result = subprocess.run(
            [sys.executable, str(LINT_SCRIPT), "--check-linter"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        status = {
            "available": result.returncode == 0,
            "empirical_linter_path": str(EMPIRICAL_LINTER_PATH),
            "lint_script_path": str(LINT_SCRIPT),
            "output": result.stdout,
            "error": result.stderr if result.stderr else None,
        }
        return json.dumps(status, indent=2)

    except Exception as e:
        return json.dumps({"available": False, "error": str(e)}, indent=2)


@mcp.resource("ignition://linter/help")
def get_linter_help() -> str:
    """Usage guide for ignition linter commands."""
    return """
Ignition Empirical Linter MCP Tools

Available Tools:
- check_linter_status: Check if empirical ignition linter is available
- lint_perspective_components: Lint Perspective view.json files
- lint_jython_scripts: Lint Python/Jython script files  
- lint_ignition_project: Comprehensive project linting
- validate_component_json: Validate single component JSON
- validate_script_content: Validate single script content

Usage Examples:
- check_linter_status()
- lint_perspective_components(project_path="ignition-projects/DemoAIProject")
- lint_jython_scripts(project_path="ignition-projects/Global", verbose=True)
- validate_component_json(component={...}, context="button_validation")

The linter provides production-validated quality checks based on analysis 
of 12,220+ real industrial components with 92.7% success rate.
    """.strip()


@mcp.tool()
def check_linter_status() -> str:
    """Check if empirical ignition linter is available and working."""
    try:
        result = subprocess.run(
            [sys.executable, str(LINT_SCRIPT), "--check-linter"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        status = {
            "available": result.returncode == 0,
            "empirical_linter_path": str(EMPIRICAL_LINTER_PATH),
            "empirical_linter_exists": EMPIRICAL_LINTER_PATH.exists(),
            "lint_script_exists": LINT_SCRIPT.exists(),
            "output": result.stdout,
            "error": result.stderr if result.stderr else None,
        }

        return json.dumps(status, indent=2)

    except Exception as e:
        return f"❌ Error checking linter status: {str(e)}"


@mcp.tool()
def lint_perspective_components(
    project_path: str, component_type: Optional[str] = None, verbose: bool = False
) -> str:
    """Lint Perspective components in an Ignition project using empirical validation."""
    cmd = [
        sys.executable,
        str(LINT_SCRIPT),
        "--project",
        project_path,
        "--type",
        "perspective",
    ]

    if component_type:
        cmd.extend(["--component", component_type])

    if verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

        error_section = f"Errors:\n{result.stderr}" if result.stderr else ""
        return (
            f"🔍 Perspective Component Linting Results\n"
            f"Project: {project_path}\n"
            f"Success: {result.returncode == 0}\n"
            f"Command: {' '.join(cmd)}\n\n"
            f"Output:\n{result.stdout}\n"
            f"{error_section}"
        )

    except Exception as e:
        return f"❌ Error linting Perspective components: {str(e)}"


@mcp.tool()
def lint_jython_scripts(project_path: str, verbose: bool = False) -> str:
    """Lint Jython/Python scripts in an Ignition project."""
    cmd = [
        sys.executable,
        str(LINT_SCRIPT),
        "--project",
        project_path,
        "--type",
        "scripts",
    ]

    if verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

        error_section = f"Errors:\n{result.stderr}" if result.stderr else ""
        return (
            f"🔍 Jython Script Linting Results\n"
            f"Project: {project_path}\n"
            f"Success: {result.returncode == 0}\n"
            f"Command: {' '.join(cmd)}\n\n"
            f"Output:\n{result.stdout}\n"
            f"{error_section}"
        )

    except Exception as e:
        return f"❌ Error linting Jython scripts: {str(e)}"


@mcp.tool()
def lint_ignition_project(
    project_path: str,
    lint_type: str = "all",
    component_type: Optional[str] = None,
    verbose: bool = False,
) -> str:
    """Comprehensive linting of entire Ignition project (both Perspective and scripts)."""
    cmd = [
        sys.executable,
        str(LINT_SCRIPT),
        "--project",
        project_path,
        "--type",
        lint_type,
    ]

    if component_type:
        cmd.extend(["--component", component_type])

    if verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

        error_section = f"Errors:\n{result.stderr}" if result.stderr else ""
        return (
            f"🔍 Ignition Project Linting Results\n"
            f"Project: {project_path}\n"
            f"Type: {lint_type}\n"
            f"Success: {result.returncode == 0}\n"
            f"Command: {' '.join(cmd)}\n\n"
            f"Output:\n{result.stdout}\n"
            f"{error_section}"
        )

    except Exception as e:
        return f"❌ Error linting Ignition project: {str(e)}"


@mcp.tool()
def validate_component_json(
    component: Dict[str, Any], context: Optional[str] = None
) -> str:
    """Validate a single Perspective component JSON against empirical schema."""
    if context is None:
        context = "component_validation"

    # Create temporary view file with the component
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_view = {"custom": {}, "params": {}, "props": {}, "root": component}
            json.dump(temp_view, f, indent=2)
            temp_path = f.name

        # Use empirical linter directly on the temp file
        empirical_perspective_linter = (
            EMPIRICAL_LINTER_PATH / "tools" / "ignition-perspective-linter.py"
        )

        if not empirical_perspective_linter.exists():
            return "❌ Empirical perspective linter not found. Please ensure the empirical-ignition-perspective-component-schema repository is available."

        cmd = [
            sys.executable,
            str(empirical_perspective_linter),
            "--target",
            temp_path,
            "--verbose",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=EMPIRICAL_LINTER_PATH
        )

        # Clean up temp file
        Path(temp_path).unlink()

        error_section = f"Errors:\n{result.stderr}" if result.stderr else ""
        return (
            f"🔍 Component Validation Results\n"
            f"Context: {context}\n"
            f"Component Type: {component.get('type', 'unknown')}\n"
            f"Success: {result.returncode == 0}\n\n"
            f"Validation Output:\n{result.stdout}\n"
            f"{error_section}"
        )

    except Exception as e:
        return f"❌ Error validating component: {str(e)}"


@mcp.tool()
def validate_script_content(script_content: str, context: Optional[str] = None) -> str:
    """Validate Jython script content against Ignition best practices."""
    if context is None:
        context = "script_validation"

    # Create temporary script file
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script_content)
            temp_path = f.name

        # Use empirical script linter directly
        empirical_script_linter = (
            EMPIRICAL_LINTER_PATH / "tools" / "ignition-script-linter.py"
        )

        if not empirical_script_linter.exists():
            return "❌ Empirical script linter not found. Please ensure the empirical-ignition-perspective-component-schema repository is available."

        cmd = [sys.executable, str(empirical_script_linter), "--target", temp_path]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=EMPIRICAL_LINTER_PATH
        )

        # Clean up temp file
        Path(temp_path).unlink()

        error_section = f"Errors:\n{result.stderr}" if result.stderr else ""
        return (
            f"🔍 Script Validation Results\n"
            f"Context: {context}\n"
            f"Script Length: {len(script_content)} characters\n"
            f"Success: {result.returncode == 0}\n\n"
            f"Validation Output:\n{result.stdout}\n"
            f"{error_section}"
        )

    except Exception as e:
        return f"❌ Error validating script: {str(e)}"


def main():
    """Main entry point for the MCP server."""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Ignition Empirical Linter MCP Server")
    parser.add_argument(
        "--http", action="store_true", help="Run as HTTP streamable server"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8008, help="Port to bind to (default: 8008)"
    )
    parser.add_argument(
        "--path", default="/mcp", help="Path for MCP endpoint (default: /mcp)"
    )

    args = parser.parse_args()

    if args.http:
        print(f"🚀 Starting Ignition Linter MCP Server (HTTP Streamable)")
        print(f"   Host: {args.host}")
        print(f"   Port: {args.port}")
        print(f"   Path: {args.path}")
        print(f"   URL: http://{args.host}:{args.port}{args.path}")

        asyncio.run(mcp.run_http_async(host=args.host, port=args.port, path=args.path))
    else:
        print("🚀 Starting Ignition Linter MCP Server (stdio)")
        mcp.run()


if __name__ == "__main__":
    main()

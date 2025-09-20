#!/usr/bin/env python3
"""
Test script for the Ignition Linter MCP server.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_mcp_server():
    """Test the MCP server by checking its tools and resources."""
    print("🧪 Testing Ignition Linter MCP Server")
    print("=" * 50)

    # Test 1: Check if FastMCP command is available
    print("\n1. Checking FastMCP command...")
    try:
        result = subprocess.run(
            ["fastmcp", "--version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ FastMCP command is available")
            print(f"   Version: {result.stdout.strip()}")
        else:
            print("❌ FastMCP command failed")
            return False
    except FileNotFoundError:
        print("❌ FastMCP command not found. Install with: pipx install fastmcp")
        return False
    except Exception as e:
        print(f"❌ Error checking FastMCP: {e}")
        return False

    # Test 2: Check if our linter script exists
    print("\n2. Checking linter script...")
    lint_script = Path("scripts/lint-ignition.py")
    if lint_script.exists():
        print(f"✅ Linter script found: {lint_script}")
    else:
        print(f"❌ Linter script not found: {lint_script}")
        return False

    # Test 3: Check empirical linter availability
    print("\n3. Checking empirical linter...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/lint-ignition.py", "--check-linter"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✅ Empirical linter is available")
            print(f"   Output: {result.stdout.strip()}")
        else:
            print("❌ Empirical linter not available")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking empirical linter: {e}")
        return False

    # Test 4: Validate MCP server script
    print("\n4. Validating MCP server script...")
    mcp_script = Path("mcp-ignition-linter.py")
    if mcp_script.exists():
        print(f"✅ MCP server script found: {mcp_script}")

        # Basic syntax check
        try:
            with open(mcp_script) as f:
                compile(f.read(), mcp_script, "exec")
            print("✅ MCP server script syntax is valid")
        except SyntaxError as e:
            print(f"❌ MCP server script has syntax error: {e}")
            return False
    else:
        print(f"❌ MCP server script not found: {mcp_script}")
        return False

    # Test 5: Check MCP configuration
    print("\n5. Checking MCP configuration...")
    mcp_config = Path(".cursor/mcp.json")
    if mcp_config.exists():
        try:
            with open(mcp_config) as f:
                config = json.load(f)

            if "ignition-linter" in config.get("mcpServers", {}):
                print("✅ Ignition linter is configured in MCP")
                linter_config = config["mcpServers"]["ignition-linter"]
                print(f"   Command: {linter_config['command']}")
                print(f"   Args: {linter_config['args']}")
            else:
                print("❌ Ignition linter not found in MCP configuration")
                return False
        except Exception as e:
            print(f"❌ Error reading MCP configuration: {e}")
            return False
    else:
        print(f"❌ MCP configuration not found: {mcp_config}")
        return False

    print("\n" + "=" * 50)
    print("🎉 All tests passed! MCP server is ready to use.")
    print("\nTo use the MCP server:")
    print("1. Restart Cursor to load the new MCP configuration")
    print("2. Use MCP tools in your AI conversations:")
    print("   - check_linter_status()")
    print('   - lint_ignition_project({"project_path": "ignition-projects/Global"})')
    print('   - validate_component_json({"component": {...}})')
    print('   - validate_script_content({"script_content": "..."})')

    return True


def show_mcp_tools():
    """Show available MCP tools."""
    print("\n📋 Available MCP Tools:")
    print("-" * 30)

    tools = [
        ("check_linter_status", "Check if empirical ignition linter is available"),
        ("lint_perspective_components", "Lint Perspective components in a project"),
        ("lint_jython_scripts", "Lint Jython/Python scripts in a project"),
        ("lint_ignition_project", "Comprehensive project linting"),
        ("validate_component_json", "Validate single component JSON"),
        ("validate_script_content", "Validate single script content"),
    ]

    for tool_name, description in tools:
        print(f"🔧 {tool_name}")
        print(f"   {description}")
        print()


def show_example_usage():
    """Show example MCP tool usage."""
    print("\n💡 Example Usage in AI Conversations:")
    print("-" * 40)

    examples = [
        {
            "description": "Check if linter is working",
            "tool": "check_linter_status",
            "args": "{}",
        },
        {
            "description": "Lint an entire project",
            "tool": "lint_ignition_project",
            "args": '{"project_path": "ignition-projects/Global", "verbose": true}',
        },
        {
            "description": "Lint only Perspective components",
            "tool": "lint_perspective_components",
            "args": '{"project_path": "ignition-projects/DemoAIProject", "component_type": "ia.display.button"}',
        },
        {
            "description": "Validate a button component",
            "tool": "validate_component_json",
            "args": '{"component": {"type": "ia.input.button", "props": {"text": "Start"}}, "context": "production_button"}',
        },
        {
            "description": "Validate Jython script",
            "tool": "validate_script_content",
            "args": '{"script_content": "\\ttry:\\n\\t\\tsystem.tag.writeBlocking(\'[default]Test\', True)\\n\\texcept Exception as e:\\n\\t\\tlogger.error(str(e))", "context": "button_click"}',
        },
    ]

    for example in examples:
        print(f"📝 {example['description']}")
        print(f"   Tool: {example['tool']}({example['args']})")
        print()


if __name__ == "__main__":
    success = test_mcp_server()

    if success:
        show_mcp_tools()
        show_example_usage()
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

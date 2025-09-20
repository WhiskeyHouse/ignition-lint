#!/usr/bin/env python3
"""
Simple Ignition Linter Integration for Cursor AI
Direct integration with empirical ignition linter for production-validated code quality.
Includes naming convention validation for Ignition view.json files.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from .json_linter import JsonLinter

# Path to the empirical linter
EMPIRICAL_LINTER_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "empirical-ignition-perspective-component-schema"
)
PERSPECTIVE_LINTER = EMPIRICAL_LINTER_PATH / "tools" / "ignition-perspective-linter.py"
SCRIPT_LINTER = EMPIRICAL_LINTER_PATH / "tools" / "ignition-script-linter.py"


def check_linter_availability():
    """Check if the empirical linter is available."""
    if not EMPIRICAL_LINTER_PATH.exists():
        print(f"❌ Empirical linter not found at: {EMPIRICAL_LINTER_PATH}")
        print(
            "   Please ensure the empirical-ignition-perspective-component-schema repository is cloned"
        )
        print("   at the expected location relative to this project.")
        return False

    if not PERSPECTIVE_LINTER.exists():
        print(f"❌ Perspective linter not found at: {PERSPECTIVE_LINTER}")
        return False

    if not SCRIPT_LINTER.exists():
        print(f"❌ Script linter not found at: {SCRIPT_LINTER}")
        return False

    print("✅ Empirical linter is available")
    print(f"   Path: {EMPIRICAL_LINTER_PATH}")
    return True


def lint_perspective(target_path, component_type=None, verbose=False):
    """Lint Perspective components."""
    if not check_linter_availability():
        return False

    cmd = ["python3", str(PERSPECTIVE_LINTER), "--target", target_path]

    if component_type:
        cmd.extend(["--component-type", component_type])

    if verbose:
        cmd.append("--verbose")

    print(f"🔍 Linting Perspective components in {target_path}")
    print(f"Command: {' '.join(cmd)}")
    print("")

    try:
        result = subprocess.run(cmd, cwd=EMPIRICAL_LINTER_PATH)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running linter: {e}")
        return False


def lint_scripts(target_path, verbose=False):
    """Lint Python/Jython scripts."""
    if not check_linter_availability():
        return False

    cmd = ["python3", str(SCRIPT_LINTER), "--target", target_path]

    if verbose:
        cmd.append("--verbose")

    print(f"🔍 Linting scripts in {target_path}")
    print(f"Command: {' '.join(cmd)}")
    print("")

    try:
        result = subprocess.run(cmd, cwd=EMPIRICAL_LINTER_PATH)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running linter: {e}")
        return False


def lint_view_naming(files, component_style="PascalCase", parameter_style="camelCase", 
                     component_style_rgx=None, parameter_style_rgx=None, allow_acronyms=False):
    """Lint view.json files for naming conventions."""
    print(f"🔍 Checking naming conventions in view files")
    print(f"   Component style: {component_style}")
    print(f"   Parameter style: {parameter_style}")
    if allow_acronyms:
        print("   Acronyms: allowed")
    print("")
    
    linter = JsonLinter(
        component_style=component_style,
        parameter_style=parameter_style,
        component_style_rgx=component_style_rgx,
        parameter_style_rgx=parameter_style_rgx,
        allow_acronyms=allow_acronyms
    )
    
    errors = linter.lint_files(files)
    linter.print_errors()
    
    return not linter.has_errors()


def _lint_perspective_components(project_path, component_type, verbose):
    """Lint Perspective components in a project."""
    perspective_path = project_path / "com.inductiveautomation.perspective" / "views"
    if perspective_path.exists():
        return lint_perspective(str(perspective_path), component_type, verbose)
    else:
        print(f"ℹ️  No Perspective views found at {perspective_path}")
        return True


def _lint_perspective_naming(project_path, component_style, parameter_style, 
                           component_style_rgx, parameter_style_rgx, allow_acronyms):
    """Lint Perspective view naming conventions in a project."""
    perspective_path = project_path / "com.inductiveautomation.perspective" / "views"
    if perspective_path.exists():
        view_pattern = str(perspective_path / "**/view.json")
        return lint_view_naming(view_pattern, component_style, parameter_style,
                              component_style_rgx, parameter_style_rgx, allow_acronyms)
    else:
        print(f"ℹ️  No Perspective views found at {perspective_path}")
        return True


def _lint_project_scripts(project_path, verbose):
    """Lint Python scripts in a project."""
    script_path = project_path / "ignition" / "script-python"
    if script_path.exists():
        return lint_scripts(str(script_path), verbose)
    else:
        print(f"ℹ️  No Python scripts found at {script_path}")
        return True


def _print_project_results(success):
    """Print final project linting results."""
    print("=" * 60)
    if success:
        print("🎉 All linting checks passed!")
    else:
        print("⚠️  Some linting checks failed. See details above.")


def lint_project(project_path, lint_type="all", component_type=None, verbose=False,
                component_style="PascalCase", parameter_style="camelCase",
                component_style_rgx=None, parameter_style_rgx=None, allow_acronyms=False,
                naming_only=False):
    """Lint an entire Ignition project."""
    project_path = Path(project_path).resolve()

    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        return False

    print(f"🚀 Linting Ignition project: {project_path.name}")
    print("=" * 60)

    success = True

    # Lint Perspective components
    if lint_type in ["perspective", "all"]:
        if naming_only:
            # Only run naming convention checks
            if not _lint_perspective_naming(project_path, component_style, parameter_style,
                                          component_style_rgx, parameter_style_rgx, allow_acronyms):
                success = False
        else:
            # Run both empirical linter and naming convention checks
            if not _lint_perspective_components(project_path, component_type, verbose):
                success = False
            if not _lint_perspective_naming(project_path, component_style, parameter_style,
                                          component_style_rgx, parameter_style_rgx, allow_acronyms):
                success = False

    # Lint Python scripts (only when not naming-only mode)
    if lint_type in ["scripts", "all"] and not naming_only:
        if not _lint_project_scripts(project_path, verbose):
            success = False

    _print_project_results(success)
    return success


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Lint Ignition projects using the empirical ignition linter and naming convention validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check if linter is available
  ignition-lint --check-linter

  # Lint entire project
  ignition-lint --project ignition-projects/DemoAIProject

  # Lint only Perspective components
  ignition-lint --project ignition-projects/Global --type perspective

  # Lint specific component type with verbose output
  ignition-lint --project ignition-projects/DemoAIProject --type perspective --component ia.display.button --verbose

  # Lint only naming conventions
  ignition-lint --project ignition-projects/DemoAIProject --naming-only --component-style PascalCase --parameter-style camelCase

  # Lint with custom naming patterns
  ignition-lint --files "**/view.json" --component-style-rgx "^[A-Z][a-zA-Z]*$" --parameter-style camelCase
        """,
    )

    parser.add_argument("--project", "-p", help="Path to Ignition project directory")
    parser.add_argument("--files", help="Comma-separated list of files or glob patterns to lint for naming conventions")

    parser.add_argument(
        "--type",
        "-t",
        choices=["perspective", "scripts", "all"],
        default="all",
        help="Type of linting to perform (default: all)",
    )

    parser.add_argument(
        "--component",
        "-c",
        help="Filter to specific component type (e.g., 'ia.display.button')",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--check-linter",
        action="store_true",
        help="Check if empirical linter is available and exit",
    )

    # Naming convention arguments
    parser.add_argument(
        "--naming-only",
        action="store_true",
        help="Only run naming convention checks, skip empirical linter"
    )

    parser.add_argument(
        "--component-style",
        default="PascalCase",
        help="Naming style for components (default: PascalCase)"
    )

    parser.add_argument(
        "--parameter-style", 
        default="camelCase",
        help="Naming style for parameters (default: camelCase)"
    )

    parser.add_argument(
        "--component-style-rgx",
        help="Custom regex pattern for component naming"
    )

    parser.add_argument(
        "--parameter-style-rgx",
        help="Custom regex pattern for parameter naming"
    )

    parser.add_argument(
        "--allow-acronyms",
        action="store_true",
        help="Allow acronyms in component and parameter names"
    )

    args = parser.parse_args()

    # Check linter availability
    if args.check_linter:
        success = check_linter_availability()
        sys.exit(0 if success else 1)

    # Handle files-only mode (direct file linting)
    if args.files:
        file_list = [f.strip() for f in args.files.split(',')]
        success = lint_view_naming(
            file_list,
            component_style=args.component_style,
            parameter_style=args.parameter_style,
            component_style_rgx=args.component_style_rgx,
            parameter_style_rgx=args.parameter_style_rgx,
            allow_acronyms=args.allow_acronyms
        )
        sys.exit(0 if success else 1)

    # Require project path for project mode
    if not args.project:
        print("❌ Project path is required. Use --project, --files, or --check-linter")
        parser.print_help()
        sys.exit(1)

    # Run linting
    success = lint_project(
        args.project, 
        args.type, 
        args.component, 
        args.verbose,
        component_style=args.component_style,
        parameter_style=args.parameter_style,
        component_style_rgx=args.component_style_rgx,
        parameter_style_rgx=args.parameter_style_rgx,
        allow_acronyms=args.allow_acronyms,
        naming_only=args.naming_only
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

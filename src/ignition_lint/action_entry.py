#!/usr/bin/env python3
"""
GitHub Actions entry point for Ignition Lint.
"""

import os
import sys
from .cli import lint_view_naming, lint_project


def main():
    """GitHub Actions entry point."""
    # Get inputs from environment variables
    files = os.getenv('INPUT_FILES', '**/view.json')
    component_style = os.getenv('INPUT_COMPONENT_STYLE', 'PascalCase')
    parameter_style = os.getenv('INPUT_PARAMETER_STYLE', 'camelCase')
    component_style_rgx = os.getenv('INPUT_COMPONENT_STYLE_RGX')
    parameter_style_rgx = os.getenv('INPUT_PARAMETER_STYLE_RGX')
    allow_acronyms = os.getenv('INPUT_ALLOW_ACRONYMS', 'false').lower() == 'true'
    project_path = os.getenv('INPUT_PROJECT_PATH')
    lint_type = os.getenv('INPUT_LINT_TYPE', 'perspective')
    naming_only = os.getenv('INPUT_NAMING_ONLY', 'true').lower() == 'true'
    
    print("🚀 Ignition Lint GitHub Action")
    print("=" * 50)
    
    success = False
    
    if project_path:
        # Project mode
        print(f"Project path: {project_path}")
        print(f"Lint type: {lint_type}")
        print(f"Naming only: {naming_only}")
        print("")
        
        success = lint_project(
            project_path=project_path,
            lint_type=lint_type,
            component_style=component_style,
            parameter_style=parameter_style,
            component_style_rgx=component_style_rgx,
            parameter_style_rgx=parameter_style_rgx,
            allow_acronyms=allow_acronyms,
            naming_only=naming_only
        )
    else:
        # Files mode
        print(f"Files: {files}")
        print("")
        
        file_list = [f.strip() for f in files.split(',')]
        success = lint_view_naming(
            file_list,
            component_style=component_style,
            parameter_style=parameter_style,
            component_style_rgx=component_style_rgx,
            parameter_style_rgx=parameter_style_rgx,
            allow_acronyms=allow_acronyms
        )
    
    # Set GitHub Actions output
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"result={'success' if success else 'failure'}\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
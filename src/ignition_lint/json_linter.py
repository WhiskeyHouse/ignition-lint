"""
JSON linter for Ignition view.json files.

Extends the functionality pioneered by Eric Knorr's ignition-lint:
https://github.com/ia-eknorr/ignition-lint

This implementation adds enhanced validation, project-wide linting,
and integration capabilities while maintaining compatibility.
"""

import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from .style_checker import StyleChecker


class ValidationError:
    """Represents a naming convention validation error."""
    
    def __init__(self, file_path: str, error_type: str, name: str, expected_style: str, location: str = ""):
        self.file_path = file_path
        self.error_type = error_type  # "component" or "parameter"
        self.name = name
        self.expected_style = expected_style
        self.location = location


class JsonLinter:
    """Lints Ignition view.json files for naming convention compliance."""
    
    def __init__(self, 
                 component_style: str = "PascalCase",
                 parameter_style: str = "camelCase",
                 component_style_rgx: Optional[str] = None,
                 parameter_style_rgx: Optional[str] = None,
                 allow_acronyms: bool = False):
        """
        Initialize the JsonLinter.
        
        Args:
            component_style: Naming style for components
            parameter_style: Naming style for parameters
            component_style_rgx: Custom regex for component names
            parameter_style_rgx: Custom regex for parameter names
            allow_acronyms: Whether to allow acronyms in names
        """
        self.component_checker = StyleChecker(component_style, allow_acronyms, component_style_rgx)
        self.parameter_checker = StyleChecker(parameter_style, allow_acronyms, parameter_style_rgx)
        self.errors: List[ValidationError] = []
        
    def lint_files(self, file_patterns: Union[str, List[str]]) -> List[ValidationError]:
        """
        Lint one or more files based on glob patterns.
        
        Args:
            file_patterns: Single pattern string or list of patterns
            
        Returns:
            List of validation errors found
        """
        self.errors = []
        
        if isinstance(file_patterns, str):
            file_patterns = [file_patterns]
            
        for pattern in file_patterns:
            files = glob.glob(pattern, recursive=True)
            for file_path in files:
                if file_path.endswith('.json') or file_path.endswith('view.json'):
                    self._lint_file(file_path)
                    
        return self.errors
    
    def _lint_file(self, file_path: str) -> None:
        """
        Lint a single JSON file.
        
        Args:
            file_path: Path to the JSON file to lint
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self._check_json_structure(data, file_path)
            
        except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError) as e:
            # Skip files that can't be parsed as JSON
            pass
    
    def _check_json_structure(self, data: Any, file_path: str, location: str = "") -> None:
        """
        Recursively check JSON structure for naming conventions.
        
        Args:
            data: JSON data to check
            file_path: Path to the file being checked
            location: Current location in the JSON structure
        """
        if isinstance(data, dict):
            # Check for component names in root and children
            if "root" in data:
                self._check_component_names(data["root"], file_path, f"{location}.root")
                
            if "children" in data:
                self._check_component_names(data["children"], file_path, f"{location}.children")
                
            # Check for parameter names in custom and params sections
            if "custom" in data:
                self._check_parameter_names(data["custom"], file_path, f"{location}.custom")
                
            if "params" in data:
                self._check_parameter_names(data["params"], file_path, f"{location}.params")
                
            # Recursively check other dictionary values
            for key, value in data.items():
                if key not in ["root", "children", "custom", "params"]:
                    self._check_json_structure(value, file_path, f"{location}.{key}" if location else key)
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check_json_structure(item, file_path, f"{location}[{i}]")
    
    def _check_component_names(self, data: Any, file_path: str, location: str) -> None:
        """
        Check component names in the JSON structure.
        
        Args:
            data: JSON data to check for component names
            file_path: Path to the file being checked
            location: Current location in the JSON structure
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "name" and isinstance(value, str):
                    if not self.component_checker.is_correct_style(value):
                        self.errors.append(ValidationError(
                            file_path, "component", value, 
                            self.component_checker.get_style_description(), location
                        ))
                else:
                    self._check_component_names(value, file_path, f"{location}.{key}")
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check_component_names(item, file_path, f"{location}[{i}]")
    
    def _check_parameter_names(self, data: Any, file_path: str, location: str) -> None:
        """
        Check parameter names in the JSON structure.
        
        Args:
            data: JSON data to check for parameter names
            file_path: Path to the file being checked
            location: Current location in the JSON structure
        """
        if isinstance(data, dict):
            for key, value in data.items():
                # Check the key itself as a parameter name
                if not self.parameter_checker.is_correct_style(key):
                    self.errors.append(ValidationError(
                        file_path, "parameter", key,
                        self.parameter_checker.get_style_description(), location
                    ))
                
                # Recursively check nested structures
                if isinstance(value, (dict, list)):
                    self._check_parameter_names(value, file_path, f"{location}.{key}")
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check_parameter_names(item, file_path, f"{location}[{i}]")
    
    def print_errors(self) -> None:
        """Print all validation errors in a formatted way."""
        if not self.errors:
            print("✅ No naming convention violations found!")
            return
            
        print(f"❌ Found {len(self.errors)} naming convention violations:")
        print("")
        
        current_file = None
        for error in sorted(self.errors, key=lambda e: (e.file_path, e.location)):
            if error.file_path != current_file:
                current_file = error.file_path
                print(f"📄 {current_file}:")
                
            print(f"  • {error.error_type.capitalize()} '{error.name}' at {error.location}")
            print(f"    Expected: {error.expected_style}")
            print("")
    
    def has_errors(self) -> bool:
        """
        Check if any validation errors were found.
        
        Returns:
            True if errors were found, False otherwise
        """
        return len(self.errors) > 0
"""
Style checker for validating naming conventions in Ignition projects.

Inspired by and compatible with the excellent work by Eric Knorr:
https://github.com/ia-eknorr/ignition-lint
"""

import re
from typing import Optional


class StyleChecker:
    """Validates naming conventions using predefined styles or custom regex patterns."""
    
    def __init__(self, style: str, allow_acronyms: bool = False, custom_regex: Optional[str] = None):
        """
        Initialize the StyleChecker.
        
        Args:
            style: The naming style to check against (snake_case, camelCase, PascalCase, UPPER_CASE, Title Case, any)
            allow_acronyms: Whether to allow acronyms in names
            custom_regex: Custom regex pattern to use instead of predefined styles
        """
        self.style = style
        self.allow_acronyms = allow_acronyms
        self.custom_regex = custom_regex
        
        # Define regex patterns for different naming styles
        self.style_patterns = {
            "snake_case": r"^[a-z]+(_[a-z]+)*$" if not allow_acronyms else r"^[a-z]+(_[a-zA-Z]+)*$",
            "camelCase": r"^[a-z]+([A-Z][a-z]*)*$" if not allow_acronyms else r"^[a-z]+([A-Z][a-zA-Z]*)*$",
            "PascalCase": r"^[A-Z][a-z]*([A-Z][a-z]*)*$" if not allow_acronyms else r"^[A-Z][a-zA-Z]*([A-Z][a-zA-Z]*)*$",
            "UPPER_CASE": r"^[A-Z]+(_[A-Z]+)*$",
            "Title Case": r"^[A-Z][a-z]*( [A-Z][a-z]*)*$" if not allow_acronyms else r"^[A-Z][a-zA-Z]*( [A-Z][a-zA-Z]*)*$",
            "any": r".*"  # Matches any string
        }
    
    def is_correct_style(self, name: str) -> bool:
        """
        Check if a name conforms to the specified style.
        
        Args:
            name: The name to check
            
        Returns:
            True if the name conforms to the style, False otherwise
        """
        if self.custom_regex:
            pattern = self.custom_regex
        else:
            pattern = self.style_patterns.get(self.style)
            
        if not pattern:
            # If style is not recognized, default to 'any'
            pattern = self.style_patterns["any"]
            
        return bool(re.match(pattern, name))
    
    def get_style_description(self) -> str:
        """
        Get a human-readable description of the current style.
        
        Returns:
            Description of the naming style
        """
        if self.custom_regex:
            return f"Custom regex: {self.custom_regex}"
        
        descriptions = {
            "snake_case": "lowercase with underscores (e.g., my_variable)",
            "camelCase": "starts lowercase, uppercase for word separation (e.g., myVariable)",
            "PascalCase": "starts uppercase, uppercase for word separation (e.g., MyClass)",
            "UPPER_CASE": "all uppercase with underscores (e.g., CONSTANT_VALUE)",
            "Title Case": "words capitalized with spaces (e.g., My Variable Name)",
            "any": "any naming style accepted"
        }
        
        base_desc = descriptions.get(self.style, f"Unknown style: {self.style}")
        if self.allow_acronyms and self.style != "any":
            base_desc += " (acronyms allowed)"
            
        return base_desc
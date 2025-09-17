#!/usr/bin/env python3
"""
Jython Whitespace and Syntax Validator for Ignition Perspective Scripts
Validates the inline Jython scripts found in JSON transforms and event handlers
"""

import ast
import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

@dataclass
class JythonIssue:
    line_number: int
    issue_type: str
    message: str
    suggestion: str
    severity: str = "warning"  # error, warning, info

class JythonValidator:
    def __init__(self):
        self.issues = []
        
    def validate_script(self, script_content: str, context: str = "") -> List[JythonIssue]:
        """Validate a Jython script for whitespace and syntax issues."""
        self.issues = []
        
        if not script_content or not script_content.strip():
            return self.issues
        
        # Analyze whitespace patterns
        self._check_indentation(script_content, context)
        
        # Check for syntax validity
        self._check_syntax(script_content, context)
        
        # Check for common Ignition patterns
        self._check_ignition_patterns(script_content, context)
        
        return self.issues
    
    def _check_indentation(self, script: str, context: str):
        """Check indentation patterns - Ignition uses tabs primarily."""
        lines = script.split('\n')
        
        # Track indentation patterns
        tab_lines = []
        space_lines = []
        mixed_lines = []
        inconsistent_levels = []
        non_indented_lines = []  # CRITICAL: Ignition requirement
        
        previous_indent_level = 0
        
        for i, line in enumerate(lines, 1):
            if not line.strip():  # Skip empty lines
                continue
                
            # Count leading whitespace
            original_line = line
            tabs = len(line) - len(line.lstrip('\t'))
            spaces_after_tabs = len(line.lstrip('\t')) - len(line.lstrip('\t').lstrip(' '))
            total_spaces = len(line) - len(line.lstrip(' '))
            
            # CRITICAL: Check Ignition requirement - ALL lines must have indentation
            if not line.startswith('\t') and not line.startswith('    '):  # No tab or 4 spaces
                non_indented_lines.append(i)
            
            # Pattern analysis
            if '\t' in line[:tabs + spaces_after_tabs]:
                if spaces_after_tabs > 0:
                    mixed_lines.append((i, original_line))
                else:
                    tab_lines.append((i, tabs))
            elif total_spaces > 0:
                space_lines.append((i, total_spaces))
            
            # Check for proper indentation progression
            current_indent = tabs + (spaces_after_tabs // 4)  # Treat 4 spaces as 1 indent level
            
            # Only check logical indentation increases (not decreases for dedents)
            if current_indent > previous_indent_level + 1:
                inconsistent_levels.append((i, current_indent, previous_indent_level))
            
            previous_indent_level = current_indent
        
        # Report CRITICAL Ignition requirement violation first
        if non_indented_lines:
            self.issues.append(JythonIssue(
                line_number=non_indented_lines[0],
                issue_type="IGNITION_INDENTATION_REQUIRED",
                message=f"Ignition requirement violation: Lines {non_indented_lines[:5]} have no indentation",
                suggestion="ALL lines in Ignition inline scripts must have at least 1 tab or 4 spaces indentation",
                severity="error"
            ))
        
        # Report issues
        if mixed_lines:
            for line_num, line_content in mixed_lines[:3]:  # Show first 3 examples
                self.issues.append(JythonIssue(
                    line_number=line_num,
                    issue_type="MIXED_INDENTATION",
                    message=f"Mixed tabs and spaces in indentation: {repr(line_content[:50])}",
                    suggestion="Use consistent tabs for indentation (Ignition standard)",
                    severity="warning"
                ))
        
        if space_lines and tab_lines:
            self.issues.append(JythonIssue(
                line_number=space_lines[0][0],
                issue_type="INCONSISTENT_INDENTATION_STYLE",
                message=f"Mixed indentation styles: {len(tab_lines)} tab lines, {len(space_lines)} space lines",
                suggestion="Use tabs consistently (matches Ignition production pattern)",
                severity="info"
            ))
        
        if inconsistent_levels:
            for line_num, current, previous in inconsistent_levels:
                self.issues.append(JythonIssue(
                    line_number=line_num,
                    issue_type="INDENTATION_JUMP",
                    message=f"Indentation jumped from {previous} to {current} levels",
                    suggestion="Increase indentation by only 1 level per logical block",
                    severity="error"
                ))
    
    def _check_syntax(self, script: str, context: str):
        """Check if the script is valid Python syntax."""
        try:
            # Try to parse as Python AST
            ast.parse(script)
        except SyntaxError as e:
            self.issues.append(JythonIssue(
                line_number=e.lineno or 1,
                issue_type="SYNTAX_ERROR",
                message=f"Python syntax error: {e.msg}",
                suggestion=f"Fix syntax error at line {e.lineno}: {e.text.strip() if e.text else ''}",
                severity="error"
            ))
        except Exception as e:
            self.issues.append(JythonIssue(
                line_number=1,
                issue_type="PARSE_ERROR",
                message=f"Could not parse script: {str(e)}",
                suggestion="Check script for fundamental syntax issues",
                severity="error"
            ))
    
    def _check_ignition_patterns(self, script: str, context: str):
        """Check for Ignition-specific patterns and best practices."""
        lines = script.split('\n')
        
        # Common Ignition system functions
        system_functions = [
            'system.perspective.sendMessage',
            'system.perspective.closePopup', 
            'system.perspective.openPopup',
            'system.net.httpClient',
            'system.date.now',
            'system.tag.read',
            'system.tag.write'
        ]
        
        # Check for common patterns
        has_system_calls = any(func in script for func in system_functions)
        has_component_navigation = any(pattern in script for pattern in ['getChild', 'getSibling', 'getParent'])
        
        # Check for potential issues
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for hardcoded localhost URLs (common issue in production)
            if 'localhost' in stripped or '127.0.0.1' in stripped:
                self.issues.append(JythonIssue(
                    line_number=i,
                    issue_type="HARDCODED_LOCALHOST",
                    message="Hardcoded localhost URL found",
                    suggestion="Use configurable host parameter or gateway setting",
                    severity="warning"
                ))
            
            # Check for print statements (should use system.perspective.print in Ignition)
            if re.search(r'\bprint\s*\(', stripped) and 'system.perspective.print' not in stripped:
                self.issues.append(JythonIssue(
                    line_number=i,
                    issue_type="PRINT_STATEMENT",
                    message="Using print() instead of system.perspective.print()",
                    suggestion="Use system.perspective.print() for Ignition console output",
                    severity="info"
                ))
            
            # Check for proper exception handling in HTTP calls
            if 'httpClient()' in stripped:
                # Look for try/catch in the script
                if 'try:' not in script or 'except' not in script:
                    self.issues.append(JythonIssue(
                        line_number=i,
                        issue_type="MISSING_EXCEPTION_HANDLING",
                        message="HTTP call without exception handling",
                        suggestion="Wrap HTTP calls in try/except blocks",
                        severity="warning"
                    ))
    
    def format_script_properly(self, script: str) -> str:
        """Format script with proper Ignition-style indentation."""
        lines = script.split('\n')
        formatted_lines = []
        current_indent = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Determine proper indent level
            if stripped.endswith(':'):
                # This line starts a block
                formatted_lines.append('\t' * current_indent + stripped)
                current_indent += 1
            elif stripped in ['else:', 'elif', 'except:', 'finally:'] or stripped.startswith(('elif ', 'except ')):
                # These reduce indent first, then may increase
                current_indent = max(0, current_indent - 1)
                formatted_lines.append('\t' * current_indent + stripped)
                if stripped.endswith(':'):
                    current_indent += 1
            elif any(stripped.startswith(keyword) for keyword in ['return', 'break', 'continue', 'pass']):
                # Statements that don't change indentation
                formatted_lines.append('\t' * current_indent + stripped)
            else:
                # Check if we're ending a block (dedent)
                original_indent = len(line) - len(line.lstrip('\t'))
                if original_indent < current_indent:
                    current_indent = original_indent
                formatted_lines.append('\t' * current_indent + stripped)
        
        return '\n'.join(formatted_lines)

def validate_jython_in_binding(binding_config: dict) -> List[JythonIssue]:
    """Validate Jython scripts in binding transforms."""
    validator = JythonValidator()
    all_issues = []
    
    transforms = binding_config.get('transforms', [])
    
    for i, transform in enumerate(transforms):
        if transform.get('type') == 'script' and 'code' in transform:
            script_code = transform['code']
            context = f"transform[{i}]"
            issues = validator.validate_script(script_code, context)
            
            # Add transform context to issues
            for issue in issues:
                issue.message = f"Transform {i}: {issue.message}"
            
            all_issues.extend(issues)
    
    return all_issues

def validate_jython_in_events(events_config: dict) -> List[JythonIssue]:
    """Validate Jython scripts in event handlers."""
    validator = JythonValidator()
    all_issues = []
    
    for event_category, handlers in events_config.items():
        if isinstance(handlers, dict):
            for event_name, handler_config in handlers.items():
                # Handle both single handler and array of handlers
                handlers_list = handler_config if isinstance(handler_config, list) else [handler_config]
                
                for j, handler in enumerate(handlers_list):
                    if isinstance(handler, dict) and handler.get('type') == 'script':
                        script_code = handler.get('config', {}).get('script', '')
                        context = f"{event_category}.{event_name}[{j}]"
                        issues = validator.validate_script(script_code, context)
                        
                        # Add event context to issues
                        for issue in issues:
                            issue.message = f"Event {event_name}: {issue.message}"
                        
                        all_issues.extend(issues)
    
    return all_issues

def main():
    """Test the validator with production examples."""
    # Test with a problematic script
    test_script = """\timport json
\t\t
\t# Define the URL
\turl = "http://127.0.0.1:6000/ask_question"
\t
\tdata = {
\t    "database": "my-db",
\t    "question": str(self.getSibling("Question").props.text)
\t}
\t
\ttry:
\t    response = system.net.httpClient().post(url, data=json.dumps(data))
\t    if response.statusCode == 200:
\t        self.getSibling("Response").props.text = response.json['response']
\texcept Exception as e:
\t    print("Error:", str(e))"""
    
    validator = JythonValidator()
    issues = validator.validate_script(test_script, "test")
    
    print("🐍 JYTHON VALIDATION RESULTS")
    print("=" * 50)
    
    for issue in issues:
        severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue.severity, "•")
        print(f"{severity_icon} Line {issue.line_number}: {issue.issue_type}")
        print(f"   {issue.message}")
        print(f"   💡 {issue.suggestion}")
        print()
    
    if not issues:
        print("✅ No issues found!")
    
    print("\n🔧 FORMATTED VERSION:")
    print("=" * 50)
    formatted = validator.format_script_properly(test_script)
    print(formatted)

if __name__ == "__main__":
    main()
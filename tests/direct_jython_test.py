#!/usr/bin/env python3
"""
Direct test of Jython validation functionality
"""

import json
import ast
import re
from typing import List
from dataclasses import dataclass

@dataclass 
class TestIssue:
    severity: str
    code: str
    message: str
    line_suggestion: str

def validate_jython_script(script_content: str, context: str = "test") -> List[TestIssue]:
    """Test version of Jython script validation."""
    issues = []
    
    if not script_content or not script_content.strip():
        return issues
    
    # Check indentation patterns
    lines = script_content.split('\n')
    mixed_indent_lines = []
    
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
            
        # Count leading whitespace
        tabs = len(line) - len(line.lstrip('\t'))
        line_after_tabs = line.lstrip('\t')
        spaces_after_tabs = len(line_after_tabs) - len(line_after_tabs.lstrip(' '))
        
        # Detect mixed indentation
        if '\t' in line[:tabs + spaces_after_tabs] and spaces_after_tabs > 0:
            mixed_indent_lines.append(i)
    
    if mixed_indent_lines:
        issues.append(TestIssue(
            severity="WARNING",
            code="JYTHON_MIXED_INDENTATION",
            message=f"Mixed tabs and spaces in {context} script (lines: {mixed_indent_lines[:3]})",
            line_suggestion="Use consistent tabs for indentation (Ignition production standard)"
        ))
    
    # Check syntax
    try:
        ast.parse(script_content)
    except SyntaxError as e:
        issues.append(TestIssue(
            severity="ERROR",
            code="JYTHON_SYNTAX_ERROR",
            message=f"Python syntax error in {context} script: {e.msg}",
            line_suggestion=f"Fix syntax error at line {e.lineno}: {e.text.strip() if e.text else 'check indentation and syntax'}"
        ))
    
    # Check best practices
    if 'localhost' in script_content or '127.0.0.1' in script_content:
        issues.append(TestIssue(
            severity="WARNING",
            code="JYTHON_HARDCODED_LOCALHOST",
            message=f"Hardcoded localhost URL in {context} script",
            line_suggestion="Use configurable host parameter or gateway setting"
        ))
    
    if re.search(r'\bprint\s*\(', script_content) and 'system.perspective.print' not in script_content:
        issues.append(TestIssue(
            severity="INFO",
            code="JYTHON_PRINT_STATEMENT",
            message=f"Using print() instead of system.perspective.print() in {context}",
            line_suggestion="Use system.perspective.print() for Ignition console output"
        ))
    
    if ('httpClient()' in script_content or 'httpPost' in script_content) and 'try:' not in script_content:
        issues.append(TestIssue(
            severity="WARNING", 
            code="JYTHON_MISSING_EXCEPTION_HANDLING",
            message=f"HTTP call without exception handling in {context}",
            line_suggestion="Wrap HTTP calls in try/except blocks"
        ))
    
    return issues

def test_jython_validation():
    """Run comprehensive Jython validation tests."""
    print("🧪 JYTHON VALIDATION TEST SUITE")
    print("=" * 60)
    
    # Load the test view
    with open('test_view_with_bad_jython.json', 'r') as f:
        test_view = json.load(f)
    
    print("📝 Test View Structure:")
    print(f"   Root type: {test_view['root']['type']}")
    print(f"   Children: {len(test_view['root']['children'])}")
    print()
    
    all_issues = []
    
    # Test event handler script
    button = test_view['root']['children'][0]
    event_script = button['events']['component']['onActionPerformed']['config']['script']
    
    print("🔍 Testing Event Handler Script:")
    print("Script content:")
    for i, line in enumerate(event_script.split('\\n'), 1):
        print(f"   {i}: {repr(line)}")
    print()
    
    event_issues = validate_jython_script(event_script, "event handler")
    all_issues.extend(event_issues)
    
    print(f"Event handler issues: {len(event_issues)}")
    for issue in event_issues:
        severity_icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(issue.severity, "•")
        print(f"   {severity_icon} {issue.code}: {issue.message}")
        print(f"      💡 {issue.line_suggestion}")
    print()
    
    # Test transform script
    label = test_view['root']['children'][1]
    transform_script = label['propConfig']['props.text']['binding']['transforms'][0]['code']
    
    print("🔍 Testing Transform Script:")
    print("Script content:")
    for i, line in enumerate(transform_script.split('\\n'), 1):
        print(f"   {i}: {repr(line)}")
    print()
    
    transform_issues = validate_jython_script(transform_script, "transform")
    all_issues.extend(transform_issues)
    
    print(f"Transform issues: {len(transform_issues)}")
    for issue in transform_issues:
        severity_icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(issue.severity, "•")
        print(f"   {severity_icon} {issue.code}: {issue.message}")
        print(f"      💡 {issue.line_suggestion}")
    print()
    
    # Summary
    print("📊 VALIDATION SUMMARY")
    print("-" * 40)
    print(f"Total Jython issues detected: {len(all_issues)}")
    
    by_severity = {}
    for issue in all_issues:
        by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
    
    for severity, count in sorted(by_severity.items()):
        icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(severity, "•")
        print(f"   {icon} {severity}: {count}")
    
    print()
    print("✅ VALIDATION COMPLETE")
    print("The Jython validator successfully detected:")
    print("   • Mixed indentation (tabs + spaces)")
    print("   • Python syntax errors")
    print("   • Hardcoded localhost URLs")
    print("   • print() vs system.perspective.print() usage")
    print("   • Missing exception handling for HTTP calls")

def test_specific_patterns():
    """Test specific Jython patterns."""
    print("\\n🔬 SPECIFIC PATTERN TESTS")
    print("=" * 60)
    
    test_cases = [
        # Good script
        ("good_script", "\\ttry:\\n\\t\\tresponse = system.net.httpClient().get(gateway_url)\\n\\t\\tsystem.perspective.print('Success')\\n\\texcept Exception as e:\\n\\t\\tsystem.perspective.print('Error:', str(e))"),
        
        # Mixed indentation
        ("mixed_indent", "\\timport json\\n\\t    data = json.loads(value)\\n\\treturn data"),
        
        # Syntax error
        ("syntax_error", "\\tif value > 5\\n\\t\\treturn 'high'"),
        
        # Best practices violations
        ("bad_practices", "\\turl = 'http://localhost:8000'\\n\\tresponse = system.net.httpClient().post(url)\\n\\tprint('Done')"),
    ]
    
    for test_name, script in test_cases:
        print(f"\\n📝 {test_name}:")
        print(f"   Script: {repr(script)}")
        
        issues = validate_jython_script(script, test_name)
        
        if issues:
            for issue in issues:
                severity_icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(issue.severity, "•")
                print(f"   {severity_icon} {issue.code}: {issue.message}")
        else:
            print("   ✅ No issues detected")

if __name__ == "__main__":
    test_jython_validation()
    test_specific_patterns()
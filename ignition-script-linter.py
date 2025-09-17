#!/usr/bin/env python3
"""
Ignition Full Script Linter

A comprehensive linting tool for Ignition script-python directories that validates:
- Jython/Python 2.7 compatibility
- Ignition system function usage
- Java integration patterns
- Common Ignition scripting best practices
- Code quality and maintainability

Usage:
    uv run python ignition-script-linter.py --target /path/to/ignition/script-python
    uv run python ignition-script-linter.py --target /path/to/ignition/script-python --verbose
    uv run python ignition-script-linter.py --target /path/to/ignition/script-python --output results.json
"""

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import importlib.util

class LintSeverity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    STYLE = "STYLE"

@dataclass
class ScriptLintIssue:
    severity: LintSeverity
    code: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        location = f":{self.line_number}" if self.line_number else ""
        return f"{self.severity.value}: {self.code} - {self.message} ({self.file_path}{location})"

class IgnitionScriptLinter:
    def __init__(self):
        self.issues: List[ScriptLintIssue] = []
        self.files_processed = 0
        self.total_lines_analyzed = 0
        
        # Ignition system modules and functions
        self.ignition_system_modules = {
            'system.alarm', 'system.bacnet', 'system.database', 'system.dataset',
            'system.date', 'system.db', 'system.device', 'system.file',
            'system.gui', 'system.iec61850', 'system.math', 'system.mongodb',
            'system.net', 'system.opcua', 'system.opc', 'system.perspective',
            'system.print', 'system.project', 'system.report', 'system.security',
            'system.tag', 'system.util', 'system.vision', 'system.webdev'
        }
        
        # Python 2.7 vs 3.x compatibility issues
        self.python2_patterns = {
            'print_statement': re.compile(r'\bprint\s+[^(]'),
            'string_types': re.compile(r'\bbasestring\b|\bunicode\b'),
            'xrange': re.compile(r'\bxrange\b'),
            'iteritems': re.compile(r'\.iteritems\(\)'),
            'iterkeys': re.compile(r'\.iterkeys\(\)'),
            'itervalues': re.compile(r'\.itervalues\(\)'),
            'has_key': re.compile(r'\.has_key\('),
            'execfile': re.compile(r'\bexecfile\b'),
            'raw_input': re.compile(r'\braw_input\b'),
            'reduce': re.compile(r'\breduce\('),
            'reload': re.compile(r'\breload\('),
        }
        
        # Common Java integration patterns in Ignition
        self.java_patterns = {
            'java_import': re.compile(r'^from\s+(java\.|com\.|org\.)\w+'),
            'java_class': re.compile(r'\b[A-Z]\w*\.[A-Z]\w*'),
            'java_method': re.compile(r'\.get[A-Z]\w*\(|\.set[A-Z]\w*\('),
        }
        
        # Common Ignition anti-patterns
        self.antipatterns = {
            'system_override': re.compile(r'^\s*system\s*='),
            'hardcoded_gateway': re.compile(r'localhost:8088|127\.0\.0\.1:8088'),
            'hardcoded_db': re.compile(r'localhost:5432|127\.0\.0\.1:5432'),
            'print_debug': re.compile(r'\bprint\s*\(.*debug|DEBUG.*\)'),
            'sleep_in_loop': re.compile(r'time\.sleep\(.+\)\s*$'),
            'global_vars': re.compile(r'^\s*global\s+\w+'),
        }

    def lint_directory(self, target_path: str, recursive: bool = True) -> Dict[str, Any]:
        """Lint all Python files in the specified directory."""
        target = Path(target_path)
        
        if not target.exists():
            raise FileNotFoundError(f"Target path does not exist: {target_path}")
        
        if not target.is_dir():
            raise ValueError(f"Target path is not a directory: {target_path}")
        
        # Find all Python files
        if recursive:
            python_files = list(target.rglob("*.py"))
        else:
            python_files = list(target.glob("*.py"))
        
        print(f"🔍 Found {len(python_files)} Python script files")
        
        # Process each file
        for i, file_path in enumerate(python_files, 1):
            if i % 50 == 0 or i == len(python_files):
                print(f"   Processing file {i}/{len(python_files)}...")
            
            self._lint_file(file_path)
        
        return self._generate_report()
    
    def _lint_file(self, file_path: Path):
        """Lint a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            self.files_processed += 1
            self.total_lines_analyzed += len(lines)
            
            # Perform various checks
            self._check_syntax(file_path, content)
            self._check_jython_compatibility(file_path, content, lines)
            self._check_ignition_patterns(file_path, content, lines)
            self._check_code_quality(file_path, content, lines)
            self._check_java_integration(file_path, content, lines)
            
        except Exception as e:
            self.issues.append(ScriptLintIssue(
                severity=LintSeverity.ERROR,
                code="FILE_READ_ERROR",
                message=f"Could not read file: {str(e)}",
                file_path=str(file_path)
            ))
    
    def _check_syntax(self, file_path: Path, content: str):
        """Check basic Python syntax."""
        try:
            # Try to parse with Python AST
            ast.parse(content)
        except SyntaxError as e:
            self.issues.append(ScriptLintIssue(
                severity=LintSeverity.ERROR,
                code="SYNTAX_ERROR",
                message=f"Python syntax error: {e.msg}",
                file_path=str(file_path),
                line_number=e.lineno,
                column=e.offset,
                suggestion=f"Fix syntax error: {e.text.strip() if e.text else 'check code structure'}"
            ))
        except Exception as e:
            self.issues.append(ScriptLintIssue(
                severity=LintSeverity.WARNING,
                code="PARSE_WARNING",
                message=f"Could not fully parse file: {str(e)}",
                file_path=str(file_path)
            ))
    
    def _check_jython_compatibility(self, file_path: Path, content: str, lines: List[str]):
        """Check for Jython/Python 2.7 compatibility issues."""
        
        # Check for Python 2 vs 3 incompatibilities
        for line_num, line in enumerate(lines, 1):
            # Check for print statements (should be print functions in Jython)
            if self.python2_patterns['print_statement'].search(line):
                self.issues.append(ScriptLintIssue(
                    severity=LintSeverity.WARNING,
                    code="JYTHON_PRINT_STATEMENT",
                    message="Print statement found - use print() function for Jython compatibility",
                    file_path=str(file_path),
                    line_number=line_num,
                    suggestion="Change 'print x' to 'print(x)'"
                ))
            
            # Check for xrange (Python 2) vs range (Python 3)
            if self.python2_patterns['xrange'].search(line):
                self.issues.append(ScriptLintIssue(
                    severity=LintSeverity.INFO,
                    code="JYTHON_XRANGE_USAGE",
                    message="xrange() found - consider using range() for consistency",
                    file_path=str(file_path),
                    line_number=line_num,
                    suggestion="xrange() works in Jython but range() is more compatible"
                ))
            
            # Check for deprecated dictionary methods
            if self.python2_patterns['iteritems'].search(line):
                self.issues.append(ScriptLintIssue(
                    severity=LintSeverity.WARNING,
                    code="JYTHON_DEPRECATED_ITERITEMS",
                    message="dict.iteritems() is deprecated - use dict.items()",
                    file_path=str(file_path),
                    line_number=line_num,
                    suggestion="Replace .iteritems() with .items()"
                ))
            
            # Check for string type issues
            if self.python2_patterns['string_types'].search(line):
                self.issues.append(ScriptLintIssue(
                    severity=LintSeverity.WARNING,
                    code="JYTHON_STRING_TYPES",
                    message="basestring/unicode types found - may cause compatibility issues",
                    file_path=str(file_path),
                    line_number=line_num,
                    suggestion="Use str type checking for better compatibility"
                ))
    
    def _check_ignition_patterns(self, file_path: Path, content: str, lines: List[str]):
        """Check for Ignition-specific patterns and best practices."""
        
        # Check for proper system module usage
        system_imports = set()
        system_calls = set()
        
        for line_num, line in enumerate(lines, 1):
            # Track system module imports
            if 'import system' in line or 'from system' in line:
                system_imports.add(line.strip())
            
            # Track system function calls
            if 'system.' in line:
                matches = re.findall(r'system\.\w+(?:\.\w+)*', line)
                system_calls.update(matches)
            
            # Check for anti-patterns
            if self.antipatterns['system_override'].search(line):
                self.issues.append(ScriptLintIssue(
                    severity=LintSeverity.ERROR,
                    code="IGNITION_SYSTEM_OVERRIDE",
                    message="Overriding 'system' variable breaks Ignition functionality",
                    file_path=str(file_path),
                    line_number=line_num,
                    suggestion="Rename variable to avoid conflict with system module"
                ))
            
            # Check for hardcoded URLs
            if self.antipatterns['hardcoded_gateway'].search(line):
                self.issues.append(ScriptLintIssue(
                    severity=LintSeverity.WARNING,
                    code="IGNITION_HARDCODED_GATEWAY",
                    message="Hardcoded gateway URL found - use system properties instead",
                    file_path=str(file_path),
                    line_number=line_num,
                    suggestion="Use system.util.getSystemProps() for gateway URL"
                ))
            
            # Check for debugging print statements
            if self.antipatterns['print_debug'].search(line):
                self.issues.append(ScriptLintIssue(
                    severity=LintSeverity.INFO,
                    code="IGNITION_DEBUG_PRINT",
                    message="Debug print statement found - consider using logger instead",
                    file_path=str(file_path),
                    line_number=line_num,
                    suggestion="Use system.util.getLogger() for proper logging"
                ))
        
        # Validate system function calls
        for call in system_calls:
            if not any(call.startswith(module) for module in self.ignition_system_modules):
                # Check if it's a known valid call or potentially invalid
                parts = call.split('.')
                if len(parts) >= 2:
                    module_path = '.'.join(parts[:2])
                    if module_path not in self.ignition_system_modules:
                        self.issues.append(ScriptLintIssue(
                            severity=LintSeverity.WARNING,
                            code="IGNITION_UNKNOWN_SYSTEM_CALL",
                            message=f"Unknown system function call: {call}",
                            file_path=str(file_path),
                            suggestion="Verify function exists in Ignition documentation"
                        ))
    
    def _check_java_integration(self, file_path: Path, content: str, lines: List[str]):
        """Check for Java integration patterns."""
        
        java_imports_found = []
        java_usage_found = []
        
        for line_num, line in enumerate(lines, 1):
            # Check for Java imports
            if self.java_patterns['java_import'].search(line):
                java_imports_found.append((line_num, line.strip()))
            
            # Check for Java-style method calls
            if self.java_patterns['java_method'].search(line):
                java_usage_found.append((line_num, line.strip()))
        
        # Report Java integration patterns (informational)
        if java_imports_found:
            self.issues.append(ScriptLintIssue(
                severity=LintSeverity.INFO,
                code="JAVA_INTEGRATION_DETECTED",
                message=f"Java imports detected ({len(java_imports_found)} imports)",
                file_path=str(file_path),
                suggestion="Ensure Java classes are available in Ignition classpath"
            ))
    
    def _check_code_quality(self, file_path: Path, content: str, lines: List[str]):
        """Check for general code quality issues."""
        
        # Check for long lines
        for line_num, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues.append(ScriptLintIssue(
                    severity=LintSeverity.STYLE,
                    code="LONG_LINE",
                    message=f"Line too long ({len(line)} characters, recommend < 120)",
                    file_path=str(file_path),
                    line_number=line_num,
                    suggestion="Break long lines for better readability"
                ))
        
        # Check for missing docstrings in functions
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not ast.get_docstring(node):
                        self.issues.append(ScriptLintIssue(
                            severity=LintSeverity.STYLE,
                            code="MISSING_DOCSTRING",
                            message=f"Function '{node.name}' missing docstring",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            suggestion="Add docstring describing function purpose and parameters"
                        ))
        except:
            pass  # Skip if AST parsing fails
        
        # Check for global variable usage
        for line_num, line in enumerate(lines, 1):
            if self.antipatterns['global_vars'].search(line):
                self.issues.append(ScriptLintIssue(
                    severity=LintSeverity.WARNING,
                    code="GLOBAL_VARIABLE_USAGE",
                    message="Global variable usage detected - consider alternatives",
                    file_path=str(file_path),
                    line_number=line_num,
                    suggestion="Use function parameters or class attributes instead"
                ))
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive linting report."""
        
        # Count issues by severity
        severity_counts = {}
        for severity in LintSeverity:
            severity_counts[severity.value] = len([i for i in self.issues if i.severity == severity])
        
        # Count issues by code
        code_counts = {}
        for issue in self.issues:
            code_counts[issue.code] = code_counts.get(issue.code, 0) + 1
        
        # Generate summary
        total_issues = len(self.issues)
        critical_issues = severity_counts.get('ERROR', 0)
        
        return {
            'summary': {
                'files_processed': self.files_processed,
                'total_lines_analyzed': self.total_lines_analyzed,
                'total_issues': total_issues,
                'critical_issues': critical_issues,
                'severity_breakdown': severity_counts,
                'most_common_issues': sorted(code_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            },
            'issues': [
                {
                    'severity': issue.severity.value,
                    'code': issue.code,
                    'message': issue.message,
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'column': issue.column,
                    'suggestion': issue.suggestion
                }
                for issue in self.issues
            ]
        }

def main():
    parser = argparse.ArgumentParser(description="Ignition Script Linter")
    parser.add_argument("--target", "-t", required=True, help="Path to Ignition script-python directory")
    parser.add_argument("--output", "-o", help="Output file for results (JSON format)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--recursive", "-r", action="store_true", default=True, help="Scan recursively (default: True)")
    
    args = parser.parse_args()
    
    print("🔍 Ignition Script Linter")
    print(f"Target: {args.target}")
    print("=" * 60)
    
    linter = IgnitionScriptLinter()
    
    try:
        report = linter.lint_directory(args.target, args.recursive)
        
        # Print summary
        summary = report['summary']
        print(f"📁 Files processed: {summary['files_processed']}")
        print(f"📝 Lines analyzed: {summary['total_lines_analyzed']}")
        print(f"🔍 Total issues: {summary['total_issues']}")
        print(f"❌ Critical issues: {summary['critical_issues']}")
        print()
        
        print("📋 Issues by severity:")
        for severity, count in summary['severity_breakdown'].items():
            emoji = {'ERROR': '❌', 'WARNING': '⚠️', 'INFO': 'ℹ️', 'STYLE': '💄'}.get(severity, '•')
            print(f"   {emoji} {severity}: {count}")
        print()
        
        if summary['most_common_issues']:
            print("🎯 Most common issues:")
            for code, count in summary['most_common_issues']:
                print(f"   {code}: {count}")
            print()
        
        # Output detailed results if requested
        if args.output:
            output_content = {
                "summary": summary,
                "detailed_issues": []
            }
            
            # Group issues by file for better readability
            issues_by_file = {}
            for issue_data in report['issues']:
                file_path = issue_data['file_path']
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
                issues_by_file[file_path].append(issue_data)
            
            for file_path, file_issues in issues_by_file.items():
                output_content["detailed_issues"].append({
                    "file": file_path,
                    "issue_count": len(file_issues),
                    "issues": file_issues
                })
            
            with open(args.output, 'w') as f:
                json.dump(output_content, f, indent=2)
            
            print(f"📝 Detailed report saved to: {args.output}")
        
        # Print some sample issues if verbose
        if args.verbose and report['issues']:
            print("🔍 Sample issues:")
            for issue_data in report['issues'][:5]:
                severity_emoji = {'ERROR': '❌', 'WARNING': '⚠️', 'INFO': 'ℹ️', 'STYLE': '💄'}.get(issue_data['severity'], '•')
                location = f":{issue_data['line_number']}" if issue_data['line_number'] else ""
                print(f"   {severity_emoji} {issue_data['code']}: {issue_data['message']}")
                print(f"      File: {issue_data['file_path']}{location}")
                if issue_data['suggestion']:
                    print(f"      Suggestion: {issue_data['suggestion']}")
                print()
        
        if summary['critical_issues'] > 0:
            print(f"❌ Linting completed with {summary['critical_issues']} critical issues")
            sys.exit(1)
        else:
            print("✅ Linting completed successfully")
            
    except Exception as e:
        print(f"❌ Error during linting: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Demo Linting Scenarios
Creates realistic Ignition components and scripts with intentional issues
to showcase the linting capabilities.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List


class LintingScenarios:
    """Demo scenarios for linting showcase."""

    def __init__(self):
        self.project_root = Path(__file__).parent

    def get_perspective_component_scenarios(self) -> List[Dict]:
        """Get Perspective component test scenarios."""
        return [
            {
                "name": "✅ Valid Start Button",
                "description": "A properly configured button component",
                "component": {
                    "type": "ia.input.button",
                    "meta": {"name": "StartProcessButton"},
                    "props": {
                        "text": "Start Process",
                        "style": {"backgroundColor": "#4CAF50", "color": "#FFFFFF"},
                    },
                    "events": {
                        "onActionPerformed": {
                            "config": {
                                "script": "\ttry:\n\t\tsystem.tag.writeBlocking('[default]Process/Command', 'START')\n\t\tlogger.info('Process started')\n\texcept Exception as e:\n\t\tlogger.error('Failed to start process: ' + str(e))"
                            }
                        }
                    },
                },
                "expected_result": "Should pass validation",
                "issues": [],
            },
            {
                "name": "❌ Button Missing Meta Name",
                "description": "Button component without required meta.name property",
                "component": {
                    "type": "ia.input.button",
                    "props": {"text": "Unnamed Button"},
                },
                "expected_result": "Should fail validation",
                "issues": ["Missing meta.name property"],
            },
            {
                "name": "❌ Invalid Component Type",
                "description": "Component with non-existent type",
                "component": {
                    "type": "ia.invalid.component",
                    "meta": {"name": "InvalidComponent"},
                    "props": {"text": "Invalid"},
                },
                "expected_result": "Should fail validation",
                "issues": ["Invalid component type"],
            },
            {
                "name": "⚠️ Button with Security Issues",
                "description": "Button that could bypass security controls",
                "component": {
                    "type": "ia.input.button",
                    "meta": {"name": "UnsafeButton"},
                    "props": {
                        "text": "Emergency Stop",
                        "style": {"backgroundColor": "#FF0000"},
                    },
                    "events": {
                        "onActionPerformed": {
                            "config": {
                                "script": "\tsystem.tag.writeBlocking('[default]Emergency/Stop', True)"
                            }
                        }
                    },
                },
                "expected_result": "May have security warnings",
                "issues": ["Emergency control without proper error handling"],
            },
            {
                "name": "⚠️ Display with Poor Color Choice",
                "description": "Display component with accessibility issues",
                "component": {
                    "type": "ia.display.label",
                    "meta": {"name": "PoorContrastLabel"},
                    "props": {
                        "text": "Status: Running",
                        "style": {"backgroundColor": "#FFFF00", "color": "#FFFFFF"},
                    },
                },
                "expected_result": "May have style warnings",
                "issues": ["Poor color contrast for readability"],
            },
        ]

    def get_jython_script_scenarios(self) -> List[Dict]:
        """Get Jython script test scenarios."""
        return [
            {
                "name": "✅ Valid Tank Control Script",
                "description": "Properly formatted Ignition script with error handling",
                "script": """\ttry:
\t\t# Read tank status
\t\ttank_status = system.tag.readBlocking('[default]Tank1/Status')
\t\tif tank_status.value == 'Ready':
\t\t\t# Start the tank process
\t\t\tsystem.tag.writeBlocking('[default]Tank1/Command', 'START')
\t\t\tlogger.info('Tank 1 started successfully')
\t\t\t
\t\t\t# Update operator display
\t\t\tsystem.tag.writeBlocking('[default]Tank1/LastStartTime', system.date.now())
\t\telse:
\t\t\tlogger.warn('Tank 1 not ready for start: ' + str(tank_status.value))
\texcept Exception as e:
\t\tlogger.error('Failed to start Tank 1: ' + str(e))
\t\t# Set alarm
\t\tsystem.tag.writeBlocking('[default]Alarms/Tank1StartFailure', True)""",
                "expected_result": "Should pass validation",
                "issues": [],
            },
            {
                "name": "❌ Script Without Indentation",
                "description": "Script that violates Ignition's indentation requirement",
                "script": """try:
    tank_status = system.tag.readBlocking('[default]Tank1/Status')
    if tank_status.value == 'Ready':
        system.tag.writeBlocking('[default]Tank1/Command', 'START')
        logger.info('Tank started')
except Exception as e:
    logger.error('Error: ' + str(e))""",
                "expected_result": "Should fail validation",
                "issues": ["Ignition requires ALL lines to be indented with tabs"],
            },
            {
                "name": "❌ Script with Mixed Indentation",
                "description": "Script mixing tabs and spaces",
                "script": """\ttry:
    \ttank_status = system.tag.readBlocking('[default]Tank1/Status')
\t    if tank_status.value == 'Ready':
\t\tsystem.tag.writeBlocking('[default]Tank1/Command', 'START')
\texcept Exception as e:
\t\tlogger.error(str(e))""",
                "expected_result": "Should fail validation",
                "issues": ["Mixed tab and space indentation"],
            },
            {
                "name": "⚠️ Script Without Error Handling",
                "description": "Script that could cause runtime errors",
                "script": """\ttank_status = system.tag.readBlocking('[default]Tank1/Status')
\tsystem.tag.writeBlocking('[default]Tank1/Command', 'START')
\tlogger.info('Tank started')""",
                "expected_result": "Should have warnings",
                "issues": ["No exception handling for tag operations"],
            },
            {
                "name": "⚠️ Script with Hardcoded Values",
                "description": "Script with maintainability issues",
                "script": """\ttry:
\t\tif system.tag.readBlocking('[default]Tank1/Level').value > 85.5:
\t\t\tsystem.tag.writeBlocking('[default]Tank1/Valve1', False)
\t\t\tsystem.tag.writeBlocking('[default]Tank1/Valve2', False)
\t\t\tsystem.tag.writeBlocking('[default]Tank1/Pump1', False)
\texcept Exception as e:
\t\tlogger.error(str(e))""",
                "expected_result": "Should have style warnings",
                "issues": ["Hardcoded threshold values", "Multiple similar operations"],
            },
            {
                "name": "❌ Script with Unknown System Call",
                "description": "Script using non-existent Ignition functions",
                "script": """\ttry:
\t\tresult = system.tag.readBlockingAdvanced('[default]Tank1/Status')
\t\tsystem.database.executeUpdateAdvanced('UPDATE tanks SET status = ?', [result])
\texcept Exception as e:
\t\tlogger.error(str(e))""",
                "expected_result": "Should fail validation",
                "issues": ["Unknown Ignition system functions"],
            },
        ]

    def create_test_view_file(self, component: Dict, filename: str = None) -> Path:
        """Create a temporary view file for testing."""
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            )
            filename = temp_file.name
            temp_file.close()

        view_structure = {"custom": {}, "params": {}, "props": {}, "root": component}

        with open(filename, "w") as f:
            json.dump(view_structure, f, indent=2)

        return Path(filename)

    def create_test_script_file(
        self, script_content: str, filename: str = None
    ) -> Path:
        """Create a temporary script file for testing."""
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            )
            filename = temp_file.name
            temp_file.close()

        with open(filename, "w") as f:
            f.write(script_content)

        return Path(filename)

    def print_scenario_summary(self):
        """Print a summary of all available scenarios."""
        print("🎯 Available Linting Demo Scenarios")
        print("=" * 50)

        print("\n📱 Perspective Component Scenarios:")
        for i, scenario in enumerate(self.get_perspective_component_scenarios(), 1):
            print(f"  {i}. {scenario['name']}")
            print(f"     {scenario['description']}")
            print(f"     Expected: {scenario['expected_result']}")
            if scenario["issues"]:
                print(f"     Issues: {', '.join(scenario['issues'])}")
            print()

        print("📝 Jython Script Scenarios:")
        for i, scenario in enumerate(self.get_jython_script_scenarios(), 1):
            print(f"  {i}. {scenario['name']}")
            print(f"     {scenario['description']}")
            print(f"     Expected: {scenario['expected_result']}")
            if scenario["issues"]:
                print(f"     Issues: {', '.join(scenario['issues'])}")
            print()


def main():
    """Main function for testing scenarios."""
    scenarios = LintingScenarios()
    scenarios.print_scenario_summary()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Analyze Ignition Perspective bindings, Jython scripts, and transforms
from production codebases to understand real-world patterns
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
import re

class BindingAnalyzer:
    def __init__(self):
        self.binding_patterns = defaultdict(list)
        self.event_patterns = defaultdict(list)
        self.transform_patterns = defaultdict(list)
        self.jython_scripts = []
        self.binding_types = Counter()
        self.transform_types = Counter()
        
    def analyze_component(self, component, file_path=""):
        """Analyze a single component for binding patterns"""
        
        # Analyze propConfig bindings
        if 'propConfig' in component:
            self.analyze_prop_config(component['propConfig'], file_path)
        
        # Analyze events (including Jython scripts)
        if 'events' in component:
            self.analyze_events(component['events'], file_path)
        
        # Recursively analyze children
        if 'children' in component:
            for child in component['children']:
                self.analyze_component(child, file_path)
    
    def analyze_prop_config(self, prop_config, file_path):
        """Analyze property configuration bindings"""
        for prop_name, config in prop_config.items():
            if 'binding' in config:
                binding = config['binding']
                binding_type = binding.get('type', 'unknown')
                self.binding_types[binding_type] += 1
                
                # Store binding pattern
                pattern = {
                    'property': prop_name,
                    'type': binding_type,
                    'config': binding.get('config', {}),
                    'file': file_path
                }
                
                # Extract transforms if present
                if 'transforms' in binding:
                    pattern['transforms'] = binding['transforms']
                    for transform in binding['transforms']:
                        transform_type = transform.get('type', 'unknown')
                        self.transform_types[transform_type] += 1
                        self.transform_patterns[transform_type].append({
                            'config': transform.get('config', {}),
                            'property': prop_name,
                            'file': file_path
                        })
                
                self.binding_patterns[binding_type].append(pattern)
    
    def analyze_events(self, events, file_path):
        """Analyze event handlers including Jython scripts"""
        for event_category, handlers in events.items():
            if isinstance(handlers, dict):
                for event_name, handler_config in handlers.items():
                    self.analyze_event_handler(event_name, handler_config, file_path, event_category)
    
    def analyze_event_handler(self, event_name, handler_config, file_path, category):
        """Analyze individual event handler"""
        # Handle both single handler and array of handlers
        handlers = handler_config if isinstance(handler_config, list) else [handler_config]
        
        for handler in handlers:
            if isinstance(handler, dict):
                handler_type = handler.get('type', 'unknown')
                config = handler.get('config', {})
                
                pattern = {
                    'event_name': event_name,
                    'category': category,
                    'type': handler_type,
                    'config': config,
                    'scope': handler.get('scope', ''),
                    'file': file_path
                }
                
                # Extract Jython scripts
                if handler_type == 'script' and 'script' in config:
                    script_content = config['script']
                    self.jython_scripts.append({
                        'script': script_content,
                        'event': event_name,
                        'file': file_path,
                        'scope': handler.get('scope', ''),
                        'lines': len(script_content.split('\n')) if script_content else 0
                    })
                
                self.event_patterns[handler_type].append(pattern)
    
    def analyze_codebase(self, base_path, codebase_name):
        """Analyze entire codebase for binding patterns"""
        print(f"🔍 Analyzing {codebase_name} for binding patterns...")
        
        view_files = list(Path(base_path).glob('**/*.json'))
        processed_files = 0
        
        for view_file in view_files:
            try:
                with open(view_file, 'r', encoding='utf-8') as f:
                    view_data = json.load(f)
                
                # Analyze root component
                if 'root' in view_data:
                    self.analyze_component(view_data['root'], str(view_file))
                elif isinstance(view_data, dict) and 'type' in view_data:
                    self.analyze_component(view_data, str(view_file))
                
                processed_files += 1
                
            except Exception as e:
                continue
        
        print(f"   Processed {processed_files} view files")
        return processed_files
    
    def generate_binding_report(self):
        """Generate comprehensive binding analysis report"""
        report = {
            'summary': {
                'total_bindings': sum(self.binding_types.values()),
                'total_transforms': sum(self.transform_types.values()),
                'total_jython_scripts': len(self.jython_scripts),
                'unique_binding_types': len(self.binding_types),
                'unique_transform_types': len(self.transform_types)
            },
            'binding_types': dict(self.binding_types),
            'transform_types': dict(self.transform_types),
            'binding_patterns': {},
            'transform_patterns': {},
            'jython_analysis': self.analyze_jython_patterns(),
            'common_patterns': self.extract_common_patterns()
        }
        
        # Convert defaultdict to regular dict for JSON serialization
        for binding_type, patterns in self.binding_patterns.items():
            report['binding_patterns'][binding_type] = patterns[:10]  # Limit examples
        
        for transform_type, patterns in self.transform_patterns.items():
            report['transform_patterns'][transform_type] = patterns[:10]  # Limit examples
        
        return report
    
    def analyze_jython_patterns(self):
        """Analyze Jython script patterns"""
        if not self.jython_scripts:
            return {}
        
        # Analyze script complexity
        script_lengths = [script['lines'] for script in self.jython_scripts]
        
        # Common imports and patterns
        common_imports = Counter()
        common_functions = Counter()
        
        for script in self.jython_scripts:
            script_content = script['script']
            if script_content:
                # Extract imports
                import_matches = re.findall(r'import\s+([^\s\n]+)', script_content)
                for imp in import_matches:
                    common_imports[imp] += 1
                
                # Extract function calls
                function_matches = re.findall(r'(\w+)\s*\(', script_content)
                for func in function_matches:
                    if len(func) > 2:  # Filter out short matches
                        common_functions[func] += 1
        
        return {
            'total_scripts': len(self.jython_scripts),
            'avg_lines': sum(script_lengths) / len(script_lengths) if script_lengths else 0,
            'max_lines': max(script_lengths) if script_lengths else 0,
            'common_imports': dict(common_imports.most_common(10)),
            'common_functions': dict(common_functions.most_common(10)),
            'script_samples': self.jython_scripts[:5]  # Sample scripts
        }
    
    def extract_common_patterns(self):
        """Extract most common binding and event patterns"""
        patterns = {}
        
        # Most common binding configurations
        if 'tag' in self.binding_patterns:
            tag_bindings = self.binding_patterns['tag']
            patterns['common_tag_paths'] = self.extract_tag_paths(tag_bindings)
        
        if 'expr' in self.binding_patterns:
            expr_bindings = self.binding_patterns['expr']
            patterns['common_expressions'] = self.extract_expressions(expr_bindings)
        
        # Most common event patterns
        if 'script' in self.event_patterns:
            script_events = self.event_patterns['script']
            patterns['common_script_events'] = Counter([
                event['event_name'] for event in script_events
            ]).most_common(10)
        
        return patterns
    
    def extract_tag_paths(self, tag_bindings):
        """Extract common tag path patterns"""
        paths = []
        for binding in tag_bindings:
            config = binding.get('config', {})
            if 'path' in config:
                paths.append(config['path'])
        
        return Counter(paths).most_common(10)
    
    def extract_expressions(self, expr_bindings):
        """Extract common expression patterns"""
        expressions = []
        for binding in expr_bindings:
            config = binding.get('config', {})
            if 'expression' in config:
                expr = config['expression']
                # Simplify expression for pattern matching
                simplified = re.sub(r'\{[^}]+\}', '{TAG}', expr)
                expressions.append(simplified)
        
        return Counter(expressions).most_common(10)

def main():
    analyzer = BindingAnalyzer()
    
    # Analyze both codebases
    distillery_path = "/Users/pmannion/Documents/whiskeyhouse/whk-distillery01-ignition-global"
    scada_path = "/Users/pmannion/Documents/whiskeyhouse/whk-ignition-scada"
    
    total_files = 0
    
    if os.path.exists(distillery_path):
        total_files += analyzer.analyze_codebase(distillery_path, "Distillery")
    
    if os.path.exists(scada_path):
        total_files += analyzer.analyze_codebase(scada_path, "SCADA")
    
    print(f"\n📊 Analysis Complete - {total_files} files processed")
    
    # Generate report
    report = analyzer.generate_binding_report()
    
    # Save detailed report
    with open("binding_analysis_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n🔍 Binding Analysis Summary:")
    print(f"   Total Bindings: {report['summary']['total_bindings']}")
    print(f"   Total Transforms: {report['summary']['total_transforms']}")
    print(f"   Total Jython Scripts: {report['summary']['total_jython_scripts']}")
    
    print(f"\n📋 Binding Types:")
    for binding_type, count in sorted(report['binding_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {binding_type}: {count}")
    
    print(f"\n🔧 Transform Types:")
    for transform_type, count in sorted(report['transform_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {transform_type}: {count}")
    
    if report['jython_analysis']['total_scripts'] > 0:
        jython = report['jython_analysis']
        print(f"\n🐍 Jython Scripts:")
        print(f"   Total Scripts: {jython['total_scripts']}")
        print(f"   Average Lines: {jython['avg_lines']:.1f}")
        print(f"   Max Lines: {jython['max_lines']}")
        
        if jython['common_imports']:
            print(f"   Common Imports: {list(jython['common_imports'].keys())[:5]}")
        
        if jython['common_functions']:
            print(f"   Common Functions: {list(jython['common_functions'].keys())[:5]}")
    
    print(f"\n📄 Detailed report saved to: binding_analysis_report.json")

if __name__ == "__main__":
    main()
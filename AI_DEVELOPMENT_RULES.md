# Ignition Perspective UI Development Rules for AI Agents

## 🎯 **Core Principles for AI-Generated UIs**

When building Ignition Perspective interfaces, follow these empirically-validated rules based on analysis of 12,220+ production components.

---

## 📋 **Essential Component Rules**

### **1. Component Structure Requirements**
```json
{
  "type": "ia.display.label",        // REQUIRED: Must be valid ia.* type
  "meta": {
    "name": "ComponentName"          // REQUIRED: Unique, descriptive name
  },
  "props": { /* component properties */ },
  "position": { /* layout properties */ }
}
```

**AI Guidelines:**
- ✅ Always include `type` and `meta.name`
- ✅ Use descriptive, camelCase names (`TankLevelIndicator`, not `Label1`)
- ❌ Never generate duplicate component names in the same view

### **2. Component Type Selection**
**Most Common Production Patterns:**
```
ia.container.flex     (35%) - Use for all layout containers
ia.display.label      (31%) - Use for text display
ia.display.icon       (6%)  - Use for status indicators  
ia.input.button       (5%)  - Use for user actions
ia.display.view       (6%)  - Use for component composition
```

**AI Decision Tree:**
- **Need layout?** → `ia.container.flex`
- **Show text/values?** → `ia.display.label` 
- **User interaction?** → `ia.input.button`
- **Status indicator?** → `ia.display.icon`
- **Data visualization?** → `ia.chart.xy` or `ia.chart.gauge`

---

## 🎨 **Layout and Positioning Rules**

### **3. Flexible Layout Properties**
```json
"position": {
  "width": 200,           // number (pixels) OR
  "width": "50%",         // string (percentage) OR  
  "width": ".5",          // string (decimal ratio)
  "grow": 1,              // number (flex grow) OR
  "grow": "Auto",         // string (auto-sizing)
  "shrink": 0             // number OR "Auto"
}
```

**AI Guidelines:**
- ✅ Use numbers for fixed pixel dimensions
- ✅ Use percentage strings for responsive layouts  
- ✅ Use flex properties (grow/shrink) for dynamic sizing
- ✅ Mix units appropriately for responsive design

### **4. Container Hierarchy**
```
Root View
├── ia.container.flex (direction: "column")
│   ├── Header: ia.container.flex (direction: "row") 
│   ├── Content: ia.container.flex (grows to fill)
│   └── Footer: ia.container.flex (direction: "row")
```

**AI Guidelines:**
- ✅ Always use `ia.container.flex` as the root container
- ✅ Set `direction: "column"` for vertical stacking
- ✅ Set `direction: "row"` for horizontal layouts
- ✅ Use nested containers for complex layouts

---

## 💾 **Data Binding and Events**

### **5. Property Binding Patterns**
```json
"propConfig": {
  "props.text": {
    "binding": {
      "type": "tag",                    // Production pattern
      "config": {
        "path": "[Tank01]Level"
      }
    }
  }
}
```

**AI Guidelines:**
- ✅ Use `tag` bindings for real-time data
- ✅ Use `expr` bindings for calculations
- ✅ Always specify meaningful tag paths
- ❌ Don't hardcode dynamic values in `props`

### **6. Event Handler Structure**
```json
"events": {
  "component": {
    "onActionPerformed": {              // Single handler
      "config": { "script": "..." },
      "scope": "G",
      "type": "script"
    }
  }
}
```

Or for multiple handlers:
```json
"events": {
  "component": {
    "onActionPerformed": [              // Multiple handlers
      { "config": {...}, "type": "script" },
      { "config": {...}, "type": "navigation" }
    ]
  }
}
```

---

## 🔍 **Quality and Performance Rules**

### **7. Accessibility Requirements**
```json
"meta": {
  "name": "TankLevelDisplay",           // Descriptive name
  "tooltip": {
    "enabled": true,
    "text": "Current tank level: 75%"     // Meaningful description
  }
}
```

**AI Guidelines:**
- ✅ Always provide descriptive component names
- ✅ Add tooltips for complex or data-bound components
- ✅ Use clear, human-readable text
- ❌ Don't use generic names like "Label1", "Button2"

### **8. Performance Optimization**
```json
"props": {
  "style": {
    "classes": "tank-indicator"        // Use CSS classes
  }
}
```

**AI Guidelines:**
- ✅ Use CSS classes instead of inline styles when possible
- ✅ Limit deep nesting (max 5 levels)
- ✅ Prefer `ia.display.view` for reusable components
- ❌ Don't duplicate identical component structures

---

## 🚨 **Common AI Pitfalls to Avoid**

### **CRITICAL: Ignition Indentation Requirement**
```python
# ❌ FATAL ERROR - Will fail in Ignition runtime
"script": "import json\nresponse = system.net.httpClient().post(url)"

# ✅ CORRECT - All lines must have indentation
"script": "\timport json\n\tresponse = system.net.httpClient().post(url)"
```

**🚨 IGNITION REQUIREMENT:** ALL lines in inline scripts must start with at least 1 tab or 4 spaces. Scripts without proper indentation will cause syntax errors and component failures.

### **Type Safety Issues**
```json
// ❌ Wrong
"props": {
  "text": 525                          // Should be string or null
}

// ✅ Correct  
"props": {
  "text": "525"                        // String for display
}
```

### **Layout Problems**
```json
// ❌ Wrong - Missing flex properties
"position": {
  "width": 100,
  "height": 50
}

// ✅ Correct - Responsive flex layout
"position": {
  "basis": "auto",
  "grow": 1,
  "shrink": 0
}
```

### **Event Handler Errors**
```json
// ❌ Wrong - Invalid event structure
"events": {
  "onClick": "doSomething()"
}

// ✅ Correct - Proper event structure
"events": {
  "component": {
    "onActionPerformed": {
      "config": {"script": "doSomething()"},
      "scope": "G",
      "type": "script"
    }
  }
}
```

---

## 🧪 **Testing and Validation**

### **9. Pre-Commit Validation**
Before generating any UI, run:
```bash
./ignition-lint path/to/view.json --format=json --severity=error
```

**AI Integration:**
- Parse JSON output for `status: "issues_found"`
- Fix any `severity: "error"` issues before proceeding
- Consider `severity: "warning"` suggestions for better UIs

### **10. Schema Compliance Check**
Ensure all components pass:
```python
# Validate against empirical schema
results = linter.lint_file("my_view.json")
assert results["schema_compliance"]["valid"] == True
```

---

## 📖 **Component-Specific Guidelines**

### **Charts and Visualization**
- Use `ia.chart.gauge` for single-value indicators
- Use `ia.chart.xy` for time series data
- Use `ia.chart.powerchart` for complex industrial data

### **Input Components**
- Use `ia.input.button` for actions
- Use `ia.input.toggle-switch` for boolean states
- Use `ia.input.numeric-entry-field` for number inputs

### **Industrial Symbols**
- Use `ia.symbol.sensor` for sensor representations
- Use `ia.symbol.valve` for valve controls
- Use `ia.display.led-display` for status indicators

---

## 🎯 **AI Success Metrics**

Your generated UIs should achieve:
- ✅ **100% schema validation** (no errors)
- ✅ **Zero accessibility issues** (proper names/tooltips)
- ✅ **Responsive layout** (proper flex usage)
- ✅ **Performance optimized** (CSS classes, minimal nesting)
- ✅ **Production patterns** (follows empirical usage data)

Run `./ignition-lint` after generation to verify compliance with these 92.7% production-validated rules.
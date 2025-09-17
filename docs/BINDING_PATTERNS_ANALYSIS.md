# Ignition Perspective Binding Patterns Analysis

## 📊 **Empirical Analysis Results**

Based on analysis of **11,092 bindings** and **679 Jython scripts** across production codebases:

---

## 🔗 **Binding Type Distribution**

| Binding Type | Count | Percentage | Use Cases |
|--------------|-------|------------|-----------|
| **expr** | 5,242 | 47.2% | Calculated values, conditional logic |
| **property** | 3,679 | 33.2% | View parameters, session data |
| **tag** | 2,067 | 18.6% | Real-time PLC/SCADA data |
| **expr-struct** | 76 | 0.7% | Complex object expressions |
| **tag-history** | 15 | 0.1% | Historical data queries |
| **query** | 13 | 0.1% | Database queries |

---

## 🛠️ **Transform Type Distribution**

| Transform Type | Count | Percentage | Common Patterns |
|----------------|-------|------------|-----------------|
| **map** | 2,512 | 70.9% | Value mapping, color coding |
| **script** | 705 | 19.9% | Complex Jython transformations |
| **expression** | 198 | 5.6% | Simple value formatting |
| **format** | 130 | 3.7% | Number/date formatting |

---

## 🎯 **Most Common Binding Patterns**

### **1. Expression Bindings (47.2%)**
```json
{
  "type": "expr",
  "config": {
    "expression": "if({[Tank01]Level} > 75, 'HIGH', if({[Tank01]Level} > 25, 'MEDIUM', 'LOW'))"
  }
}
```

**Common Expression Patterns:**
- Conditional logic: `if({value} > threshold, 'A', 'B')`
- String concatenation: `'Label: ' + {value}`
- Mathematical operations: `{value1} * {value2} / 100`
- Quality checks: `if({tag.quality} = 'Good', {tag.value}, 'Bad Quality')`

### **2. Property Bindings (33.2%)**
```json
{
  "type": "property", 
  "config": {
    "path": "view.params.tankId"
  },
  "transforms": [
    {
      "type": "expression",
      "expression": "'Tank: ' + {value}"
    }
  ]
}
```

**Common Property Paths:**
- View parameters: `view.params.*`
- Session data: `session.props.auth.user.*`
- Page properties: `page.props.dimensions.viewport.*`
- Component state: `this.custom.*`

### **3. Tag Bindings (18.6%)**
```json
{
  "type": "tag",
  "config": {
    "tagPath": "[Production]Line01/Tank/Level",
    "mode": "direct",
    "fallbackDelay": 2.5
  },
  "transforms": [
    {
      "type": "format",
      "config": {
        "pattern": "#,##0.##"
      }
    }
  ]
}
```

**Tag Binding Patterns:**
- Direct mode: `"mode": "direct"` (most common)
- Indirect mode: `"mode": "indirect"` with references
- Fallback handling: `"fallbackDelay": 2.5`
- Quality monitoring: Built-in quality checking

---

## 🔧 **Transform Patterns**

### **1. Map Transforms (70.9%)**
Most common for value-to-value mappings:

```json
{
  "type": "map",
  "inputType": "scalar",
  "outputType": "color",
  "fallback": "#808080",
  "mappings": [
    {"input": 0, "output": "#FF0000"},
    {"input": 1, "output": "#00FF00"},
    {"input": 2, "output": "#0000FF"}
  ]
}
```

**Common Map Transform Uses:**
- Status colors: Numbers → Colors
- State text: Numbers → Descriptive strings  
- Alarm levels: Values → Priority levels
- Equipment states: Codes → Human-readable text

### **2. Script Transforms (19.9%)**
Complex logic requiring Jython:

```json
{
  "type": "script",
  "code": "if value == 0 or value > 750:\n\tmode = 'browser'\nelse:\n\tmode = 'mobile'\nself.setCanvasMode(mode)\nreturn mode"
}
```

**Script Transform Patterns:**
- Mode switching based on screen size
- Complex calculations with multiple inputs
- Custom formatting beyond standard options
- Integration with external systems

### **3. Expression Transforms (5.6%)**
Simple value formatting:

```json
{
  "type": "expression", 
  "expression": "if({value} = null, '--', numberFormat({value}, '#,##0.##%'))"
}
```

---

## 🐍 **Jython Script Analysis**

### **Script Usage Statistics**
- **Total Scripts:** 679
- **Average Length:** 5.6 lines
- **Longest Script:** 180 lines  
- **Most Complex:** HTTP API integration scripts

### **Most Common Functions**
| Function | Usage Count | Purpose |
|----------|-------------|---------|
| `getChild()` | 398 | Navigate component hierarchy |
| `write()` | 230 | Update component properties |
| `sendMessage()` | 131 | Inter-component communication |
| `closePopup()` | 88 | Close popup windows |
| `print()` | 87 | Debug logging |
| `getSibling()` | 52 | Access sibling components |

### **Common Script Patterns**

#### **1. Component Navigation & Updates**
```python
# Most common pattern (398 uses)
tank_level = self.getChild("TankLevel")
tank_level.props.text = str(new_value)
```

#### **2. Message Passing**
```python
# Inter-component communication (131 uses)
system.perspective.sendMessage('refresh-data', {'timestamp': system.date.now()})
```

#### **3. Popup Management**
```python
# Popup control (88 uses) 
system.perspective.closePopup('equipment-details')
```

#### **4. HTTP API Integration**
```python
# External system integration
import json
url = "http://127.0.0.1:6000/ask_question"
data = {"database": "production", "query": user_input}
response = system.net.httpPost(url, data)
```

### **Common Imports**
- `json` - JSON data handling
- `Message` - Custom message classes
- `work_order_task` - CMMS integration
- `inventory` - Inventory management
- `time` - Time manipulation

---

## 📋 **Binding Schema Implications**

### **Required Binding Structure**
```json
{
  "type": "expr|property|tag|expr-struct|tag-history|query",
  "config": {
    // Type-specific configuration
  },
  "transforms": [
    {
      "type": "map|script|expression|format",
      // Transform-specific configuration
    }
  ]
}
```

### **Property-Specific Patterns**

#### **Tag Bindings**
```json
{
  "type": "tag",
  "config": {
    "tagPath": "string (required)",
    "mode": "direct|indirect",
    "fallbackDelay": "number",
    "references": "object (for indirect mode)"
  }
}
```

#### **Expression Bindings**  
```json
{
  "type": "expr",
  "config": {
    "expression": "string (required)"
  }
}
```

#### **Property Bindings**
```json
{
  "type": "property", 
  "config": {
    "path": "string (required)"
  }
}
```

### **Transform Schema Patterns**

#### **Map Transforms**
```json
{
  "type": "map",
  "inputType": "scalar|array|dataset",
  "outputType": "scalar|color|object",
  "fallback": "any",
  "mappings": [
    {"input": "any", "output": "any"}
  ]
}
```

#### **Script Transforms**
```json
{
  "type": "script",
  "code": "string (Jython code)"
}
```

---

## 🚀 **Best Practices for AI Development**

### **1. Binding Selection Guidelines**
- **Static data/parameters:** Use `property` bindings
- **Real-time PLC data:** Use `tag` bindings with fallback handling
- **Calculated values:** Use `expr` bindings
- **Complex logic:** Use `script` transforms
- **Simple mappings:** Use `map` transforms

### **2. Performance Optimization**
- Prefer `map` transforms over `script` transforms when possible
- Use `direct` tag mode unless references needed
- Keep Jython scripts under 10 lines when possible
- Cache expensive calculations in custom properties

### **3. Error Handling Patterns**
```json
{
  "type": "expr",
  "config": {
    "expression": "if({tag.quality} = 'Good', {tag.value}, 'No Data')"
  }
}
```

### **4. Common Anti-Patterns to Avoid**
- ❌ Hardcoding values that should be dynamic
- ❌ Complex scripts for simple value mapping
- ❌ Missing fallback values in tag bindings
- ❌ Overly complex nested expressions

---

## 📊 **Production Validation Statistics**

- **11,092 bindings analyzed** across 3,090 view files
- **6 binding types** validated
- **4 transform types** identified  
- **679 Jython scripts** analyzed (avg 5.6 lines)
- **3,545 transforms** with complex logic

This empirical analysis provides the foundation for robust binding validation and AI-guided development patterns.
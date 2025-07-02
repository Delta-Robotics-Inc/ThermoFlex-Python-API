# Version Checking Implementation

**Date:** June 30, 2025  
**Type:** Feature Implementation  
**Impact:** Low - User Experience Enhancement

## Overview

Implemented automatic firmware version checking to warn users about compatibility issues when ThermoFlex nodes are first discovered. This addresses the TODO item for version checking with helpful warnings and links to update resources.

## Features Implemented

### ✅ **Automatic Version Checking**

**When it runs:**
- Automatically triggered when a node is first discovered
- Runs once per node when firmware version is first retrieved via dump status
- Uses a flag (`_version_check_completed`) to prevent repeated warnings

**Compatibility Rules:**
```python
MIN_FIRMWARE_VERSION = "1.1.0"      # Minimum supported firmware
MAX_TESTED_FIRMWARE_VERSION = "1.2.99"  # Maximum tested firmware
```

### ✅ **Smart Warning Messages**

**Firmware Too Old (< 1.1.1):**
```
⚠️  WARNING: Node 1.0.17 Firmware Update Required (in yellow text)
   Current firmware: v1.0.15
   Minimum required: v1.1.1
   
   Your controller firmware is out of date and may not work
   correctly with this Python library version.
   
   Please update your firmware:
   https://github.com/Delta-Robotics-Inc/ThermoFlex-Firmware/releases
```

**Firmware Too New (> 1.1.2):**
```
⚠️  WARNING: Node 1.0.17 Firmware May Be Too New (in yellow text)
   Current firmware: v1.3.0
   Max tested version: v1.1.2
   
   Your controller firmware is newer than what this Python
   library has been tested with. Some features may not work
   correctly.
   
   Consider updating the Python library:
   pip install -U thermoflex
```

**Compatible Firmware:**
```
✅ Node 1.0.17: Firmware v1.1.1 is compatible (in green text)
```

### ✅ **Version Parsing & Comparison**

**New Utility Functions:**
- `parse_version(version_str)` - Parses version strings into comparable tuples
- `compare_versions(v1, v2)` - Compares two version strings (-1, 0, 1)

**Supports Both Formats:**
- Legacy X.X format: "1.2" 
- New X.X.X format: "1.2.13"

## Implementation Details

### **Node Class Enhancement**

```python
class Node:
    def __init__(self, ...):
        # Version checking flag
        self._version_check_completed = False
        
    def _check_firmware_version(self):
        """Check firmware compatibility and warn user"""
        # Only runs once per node
        # Compares against MIN/MAX version constants
        # Displays colored warning messages (yellow for warnings, green for OK)
        
    def updateStatus(self, inc_data):
        # Calls _check_firmware_version() when firmware is first parsed
        self.firmware = f"{major}.{minor}.{patch}"
        self._check_firmware_version()  # ← Added here
```

### **Configuration Constants**

Version compatibility ranges defined at module level:
```python
MIN_FIRMWARE_VERSION = "1.1.0"
MAX_TESTED_FIRMWARE_VERSION = "1.2.99" 
FIRMWARE_UPDATE_URL = "https://github.com/YourOrg/ThermoFlex-Firmware/releases"
PYTHON_UPDATE_URL = "https://github.com/YourOrg/ThermoFlex-Python/releases"
```

## Testing

### **Demo Script Created**

`test/version_check_demo.py` demonstrates:
- Automatic version checking during node discovery
- One-time execution per node
- Version compatibility status display
- Access to version checking configuration

### **Example Output**

```bash
$ python test/version_check_demo.py

=== THERMOFLEX VERSION CHECK DEMO ===

Discovering ThermoFlex devices...
✅ Node 1.0.17: Firmware v1.2.13 is compatible

📊 Node Information:
   Node ID: 1.0.17
   Firmware Version: 1.2.13
   Board Version: 2.1
   Supply Voltage: 22.15V

⚙️  Version Compatibility Configuration:
   Minimum Supported: v1.1.0
   Maximum Tested: v1.2.99
```

## Benefits

### **User Experience**
- **Proactive Warnings**: Users are immediately notified of compatibility issues
- **Clear Guidance**: Specific instructions and links for resolving issues
- **Non-Intrusive**: Only runs once per node, doesn't slow down operations

### **Developer Experience**
- **Easy Configuration**: Version ranges easily adjustable via constants
- **Comprehensive**: Handles both old firmware and new firmware scenarios
- **Backward Compatible**: Works with both X.X and X.X.X version formats

## Future Enhancements

- **Online Version Checking**: Could check for latest firmware versions online
- **Version Database**: Maintain compatibility database for specific feature sets
- **Update Integration**: Direct integration with firmware update tools

## Node Discovery Enhancement

**UPDATE**: Enhanced the automatic discovery process to ensure version checking happens immediately when nodes are discovered:

### **Automatic Dump Status Requests**

**`refreshDevices()` Enhancement:**
```python
def refreshDevices(self):
    # Request compact status for basic discovery  
    self.broadcast_node.status('compact', device='all')
    
    # ADDED: Request dump status for firmware version checking
    self.broadcast_node.status('dump', device='node')  # ← Triggers version check
```

**`add_node()` Enhancement:**
```python  
def add_node(self, node_id: list[int]) -> 'Node':
    # Create new node
    node = Node(len(self.active_nodes) + 1, self, n_id=node_id)
    self.active_nodes[node_id_tuple] = node
    
    # ADDED: Request dump status from newly discovered node
    node.status('dump', device='node')  # ← Triggers version check
    
    return node
```

### **Verified in Multiple Tests**

The enhancement has been verified to work automatically in:
- `device-status-dump.py` - ✅ Shows version warning during discovery
- `muscle-cmd-test.py` - ✅ Shows version warning during discovery  
- `accessor_methods_demo.py` - ✅ Shows version warning during discovery

**No test modifications required** - version checking now happens automatically in ALL scripts that discover nodes.

## Summary

This implementation provides users with immediate, helpful feedback about firmware compatibility issues, making the ThermoFlex Python library more user-friendly and reducing support burden from version-related problems.

The version checking runs **automatically during the normal node discovery process**, requires no user intervention, and only displays warnings when actual compatibility issues are detected. Users will see firmware compatibility warnings immediately when connecting to any ThermoFlex device, without needing to explicitly request dump status. 
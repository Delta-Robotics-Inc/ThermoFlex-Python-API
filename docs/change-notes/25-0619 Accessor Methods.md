# ThermoFlex Accessor Methods

## Overview

This document describes the new accessor methods added to the `Node` and `Muscle` classes to provide a clean, type-safe interface for accessing status data without error-prone dictionary access.

## Problem with Dictionary Access

**Before** (error-prone):
```python
# ❌ Wrong field name - causes None values
voltage = node.node_status.get('v_supply')

# ✅ Correct but fragile - requires internal knowledge
voltage = node.node_status.get('volt_supply')

# ❌ IndexError risk with list values
current = node.muscle0.SMA_status.get('load_amps', [])[0]
```

## Solution: Accessor Methods

**After** (clean and safe):
```python
# ✅ Clean, self-documenting, and safe
voltage = node.get_supply_voltage()
current = node.muscle0.get_current()
```

## Node Accessor Methods

### Basic Status
```python
node.get_supply_voltage() -> float      # Supply voltage in volts
node.get_uptime() -> int               # Uptime in milliseconds
node.get_error_code() -> int           # Most recent error code
node.get_error_history() -> list       # Complete error history
node.has_errors() -> bool              # True if any errors exist
```

### Device Information
```python
node.get_node_id_string() -> str       # Formatted node ID ("1.0.17")
node.get_firmware_version() -> str     # Firmware version
node.get_board_version() -> str        # Board version  
node.get_can_id() -> int              # CAN bus ID
node.get_node_active_status() -> bool  # Node heartbeat status
```

### Sensor Data
```python
node.get_potentiometer_value() -> float    # Potentiometer reading
node.get_log_interval() -> int             # Log interval in ms
```

### Configuration (dump status)
```python
node.get_max_current() -> float            # Maximum current limit
node.get_min_supply_voltage() -> float     # Minimum voltage threshold
node.get_voltage_divider_scalar() -> float # VRD scalar value
node.get_voltage_divider_offset() -> float # VRD offset value
```

## Muscle Accessor Methods

### Status Information
```python
muscle.is_enabled() -> bool            # Enable status
muscle.get_mode() -> int              # Control mode (enum)
muscle.get_setpoint() -> float        # Current setpoint value
muscle.get_port_number() -> int       # Port number (0-based)
muscle.get_device_port() -> int       # Device port enum
muscle.get_muscle_id() -> str         # Formatted muscle ID
```

### Real-time Data
```python
muscle.get_current() -> float         # Most recent current (amps)
muscle.get_voltage_drop() -> float    # Most recent voltage drop (volts)
muscle.get_resistance() -> float      # Most recent resistance (milliohms)
muscle.get_output_pwm() -> float      # PWM output value
```

### Historical Data
```python
muscle.get_current_history() -> list      # All current readings
muscle.get_resistance_history() -> list   # All resistance readings
```

### Control Information (dump status)
```python
muscle.get_default_mode() -> int          # Default control mode
muscle.get_default_setpoint() -> float    # Default setpoint
muscle.get_pid_kp() -> float             # PID proportional gain
muscle.get_pid_ki() -> float             # PID integral gain
muscle.get_pid_kd() -> float             # PID derivative gain
muscle.get_train_state() -> int          # Training state
```

### Advanced Diagnostics (dump status)
```python
muscle.get_voltage_load_scalar() -> float  # VLD scalar
muscle.get_voltage_load_offset() -> float  # VLD offset
muscle.get_sense_resistance() -> float     # Sense resistance (ohms)
muscle.get_amplifier_gain() -> float       # Amplifier gain
```

## Benefits

1. **Type Safety**: Methods include type hints for better IDE support
2. **Error Prevention**: No more field name confusion (volt_supply vs v_supply)
3. **Robust List Handling**: Built-in handling for list vs scalar values
4. **Self-Documenting**: Clear, descriptive method names
5. **Comprehensive Documentation**: Each method includes detailed docstrings
6. **Future-Proof**: API can handle protocol changes transparently

## Usage Example

```python
import thermoflex as tf

# Get node
node = tf.get_usb_node()

# Request status
node.status('compact', device='all')

# Access data using clean methods
print(f"Node {node.get_node_id_string()}")
print(f"Supply: {node.get_supply_voltage():.2f}V")
print(f"Uptime: {node.get_uptime()}ms")

# Access muscle data
muscle = node.muscle0
print(f"Muscle {muscle.get_muscle_id()}")
print(f"Current: {muscle.get_current():.3f}A")
print(f"Enabled: {muscle.is_enabled()}")
```

## Migration Guide

### Old Code (Dictionary Access)
```python
# Node status
voltage = node.node_status.get('volt_supply')
uptime = node.node_status.get('uptime')
errors = node.node_status.get('errors', [])

# Muscle status  
current_list = muscle.SMA_status.get('load_amps', [])
current = current_list[0] if current_list else None
enabled = muscle.SMA_status.get('enabled')
```

### New Code (Accessor Methods)
```python
# Node status
voltage = node.get_supply_voltage()
uptime = node.get_uptime() 
has_errors = node.has_errors()

# Muscle status
current = muscle.get_current()  # Handles list/scalar automatically
enabled = muscle.is_enabled()
```

## Demo Script

Run `python accessor_methods_demo.py` to see all accessor methods in action and compare the old vs new approaches. 
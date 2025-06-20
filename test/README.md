# ThermoFlex Python Library Test Suite

This directory contains test scripts and validation tools for the ThermoFlex Python library. All tests have been updated to use **protocol-compliant field names** matching the protobuf definitions.

## Test Categories

### ✅ **Core Functionality Tests**
- `muscle-cmd-test.py` - Comprehensive muscle command and status testing
- `device_targeting_test.py` - Device targeting functionality validation  
- `packet_protocol_compliance_test.py` - Protocol compliance validation
- `Testsess.py` - Session logging and training sequence testing

### 🔍 **Node Validation** (`node-validation/`)
- `read_voltage.py` - Supply voltage consistency validation
- `no_load_current.py` - No-load current baseline measurement
- `current_pulse.py` - Current control response validation

## Quick Test Commands

### Basic Functionality Test
```bash
python muscle-cmd-test.py
```
Tests muscle commands, status monitoring, and protocol-compliant field access.

### Protocol Compliance Check
```bash
python packet_protocol_compliance_test.py
```
Validates that packet parsing uses correct protobuf field names.

### Device Targeting Test
```bash
python device_targeting_test.py
```
Tests different device targeting options (all, node, portall, individual muscles).

### Sensor Validation (Multiple Commands)
```bash
cd node-validation
python read_voltage.py --duration 10 --outfile voltages.csv
python no_load_current.py --duration 10 --outfile idle_current.csv
python current_pulse.py --target 2.5 --pulse 1.0 --duration 5 --outfile pulse.csv
```

## Protocol Compliance Updates

All tests have been updated to use **standard protobuf field names**:

| **Purpose** | **Protocol Field** | **Legacy Field** | **Status** |
|-------------|-------------------|------------------|------------|
| Enable Status | `enabled` | ~~`enable_status`~~ | ✅ Updated |
| Control Mode | `mode` | ~~`control_mode`~~ | ✅ Updated |
| Current Setpoint | `setpoint` | ~~Missing~~ | ✅ Added |
| PWM Output | `output_pwm` | ~~`pwm_out`~~ | ✅ Updated |
| Voltage Drop | `load_vdrop` | ~~`load_voltdrop`~~ | ✅ Updated |
| Device Port | `device_port` | ~~`dev`~~ | ✅ Updated |

## Test Results

### ✅ **Passing Tests**
- **Protocol compliance**: 8/8 expected fields present, 0 legacy fields found
- **Device targeting**: All targeting modes working correctly
- **Current readings**: Consistent data reception using `load_amps` field
- **Field naming**: 100% protocol-compliant field names

### ⚠️ **Known Issues**
- **Setpoint data quality**: Firmware sends uninitialized data for `setpoint` field (garbage values like `-2.1e+26`)
  - **Impact**: Field exists and is received correctly, but contains invalid data
  - **Workaround**: Tests use fallback to `default_setpoint` or configured values

## Test Environment

### Requirements
- Python 3.7+
- ThermoFlex Python library (latest version)
- Connected ThermoFlex node via USB
- Appropriate safety measures for current testing

### Hardware Setup
- ThermoFlex controller connected via USB
- Optional: SMA actuators for load testing
- Optional: Multiple nodes for validation testing

## Safety Guidelines

### ⚠️ **Current Testing Safety**
- Start with low currents (< 1A) to verify operation
- Monitor for overheating during tests
- Use appropriate loads rated for test currents
- Supervise all tests - do not leave unattended
- Have emergency stop procedures ready

### 🔧 **General Testing**
- Verify all connections before testing
- Ensure stable power supply
- Check for proper grounding
- Respect device current and voltage limits

## Debugging Failed Tests

### No Node Found
```bash
# Check USB connection and try:
python -c "import thermoflex as tf; node = tf.get_usb_node(timeout=15.0); print(f'Found: {node.id}')"
```

### Protocol Compliance Issues
```bash
# Run detailed protocol check:
python packet_protocol_compliance_test.py
```

### Current Reading Issues
```bash
# Check basic current reading:
python -c "
import thermoflex as tf
import time
node = tf.get_usb_node()
node.status('compact', device='all')
time.sleep(1)
print('Load amps:', node.muscle0.SMA_status.get('load_amps'))
"
```

## Development

### Adding New Tests
1. Use protocol-compliant field names (`enabled`, `load_amps`, `load_vdrop`, etc.)
2. Include proper error handling and cleanup
3. Follow the modern API patterns (`tf.get_usb_node()`, `node.status()`)
4. Add comprehensive documentation

### Test Naming Convention
- `*_test.py` - Functional tests
- `*_validation.py` - Hardware validation scripts  
- `*_compliance.py` - Protocol/standard compliance checks

## Migration from Legacy Tests

### Removed Tests
- `debug_muscle_status.py` - Replaced by `packet_protocol_compliance_test.py`
- `heartbeattest.py` - Outdated discovery method
- `node-cmd-test.py` - Empty stub file
- `current_reading_diagnostic.py` - Debugging script no longer needed

### Field Name Updates
If updating existing code, replace:
```python
# OLD - Legacy field names
muscle.SMA_status['enable_status']  → muscle.SMA_status['enabled']
muscle.SMA_status['control_mode']   → muscle.SMA_status['mode']  
muscle.SMA_status['pwm_out']        → muscle.SMA_status['output_pwm']
muscle.SMA_status['load_voltdrop']  → muscle.SMA_status['load_vdrop']
node.node_status['volt_supply']     → node.node_status['v_supply']
```

## Support

### Test Issues
1. Check hardware connections
2. Verify latest library version
3. Review test output for specific errors
4. Check that node firmware is responsive

### Protocol Issues  
1. Run protocol compliance test
2. Check for firmware updates
3. Verify protobuf definitions match firmware
4. Report any field naming discrepancies

---

**Note**: All tests are designed to work with the protocol-compliant packet parsing implemented in the main library. They will accurately reflect the current state of firmware protocol compliance and can be used to validate firmware updates. 
# Raw Supply Voltage Sensor Addition - 2025-06-30

## Overview
Added support for raw ADC supply voltage readings across the ThermoFlex system for enhanced sensor validation and calibration analysis.

## Changes Made

### 1. Protobuf Definition Update
**File:** `python-serial/src/thermoflex/tools/tfnode-messages.proto`
- Added `uint32 v_supply_raw = 14;` to `NodeStatusDump` message
- Provides raw ADC reading for supply voltage before scaling
- Regenerated `tfnode_messages_pb2.py` using protoc compiler

### 2. Node Controller Enhancement  
**File:** `python-serial/src/thermoflex/devices.py`
- Added `'v_supply_raw':None` to Node `node_status` dictionary initialization
- Added `get_supply_voltage_raw() -> int` accessor method
- Existing `updateStatus()` method automatically handles the new field via direct field matching

### 3. Validation Script Updates
Updated all validation scripts to include raw supply voltage in CSV output:

**File:** `test/node-validation/muscle_measurement.py`
- Added `supply_voltage_raw` column to CSV header
- Updated data collection to retrieve raw supply voltage using `node.get_supply_voltage_raw()`
- Updated data row writing to include raw supply voltage value
- Updated error row writing to include "ERROR" placeholder for raw supply voltage

**File:** `test/node-validation/val_supply_voltage.py`  
- Added `supply_voltage_raw` column to CSV header
- Updated data collection to retrieve raw supply voltage
- Updated data row writing to include raw supply voltage value

**File:** `test/node-validation/validation_flow.py`
- Added `supply_v_raw` column to CSV header  
- Updated data collection to retrieve raw supply voltage
- Updated data row writing to include raw supply voltage value

### 4. Session Logging Compatibility
**File:** `python-serial/src/thermoflex/sessions.py`
- No changes required - existing logging automatically captures raw supply voltage
- Session file logging calls `node.getStatus()` which includes all `node_status` fields
- Raw supply voltage data will be included in logged status strings

## Benefits

### Enhanced Validation Capabilities
- Raw ADC values enable detection of scaling/calibration errors
- Comparison between scaled voltage and raw ADC readings identifies sensor drift
- Cross-controller calibration validation with raw sensor data

### Improved Debugging
- Raw sensor values help diagnose ADC issues vs. scaling problems
- Better understanding of sensor noise and resolution characteristics
- Enhanced troubleshooting for supply voltage measurement discrepancies

### Validation Test Enhancement
- All validation scripts now capture both scaled and raw supply voltage
- CSV output includes complete sensor data for comprehensive analysis
- Test metadata preserved for validation traceability

## Usage

### Accessing Raw Supply Voltage
```python
# Get raw ADC reading
raw_adc = node.get_supply_voltage_raw()

# Get scaled voltage for comparison  
scaled_voltage = node.get_supply_voltage()
```

### CSV Output
All validation scripts now include `supply_voltage_raw` or `supply_v_raw` columns containing the raw ADC readings alongside the scaled voltage values.

## Backward Compatibility
- Fully backward compatible with existing firmware/protobuf versions
- Raw supply voltage field gracefully handles `None` values when not available
- Existing validation data analysis tools continue to work unchanged
- New raw voltage data provides additional validation capability without breaking existing functionality 
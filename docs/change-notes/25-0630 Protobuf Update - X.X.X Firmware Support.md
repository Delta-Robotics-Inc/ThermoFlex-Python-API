# Protocol Buffer Update - X.X.X Firmware Version Support

**Date:** June 30, 2025  
**Type:** Protocol Update, Breaking Changes  
**Impact:** High - Firmware version format changed, device port enumeration changed

## Overview

Updated the ThermoFlex Node protobuf definition to support the full firmware version format (X.X.X) that the new v1.1.1 firmware provides, along with other protocol enhancements and breaking changes.

## Key Changes

### ✅ **New Firmware Version Format (X.X.X)**

**Before (X.X format only):**
```protobuf
message NodeStatusDump {
    uint32 firmware_version = 3;        // major
    uint32 firmware_subversion = 4;     // minor
}
```

**After (X.X.X format):**
```protobuf
message NodeStatusDump {
    uint32 firmware_version_major = 3;
    uint32 firmware_version_minor = 4;
    uint32 firmware_version_patch = 13;
}
```

**API Enhancement:**
- `get_firmware_version()` now returns full "1.2.13" format instead of "1.2"
- Backward compatibility maintained for legacy X.X format
- Validation scripts now include full firmware version in output

### ⚠️ **Breaking Changes**

#### 1. Device Port Enumeration Changed
```protobuf
// OLD:
DEVICE_PORT1 = 3;  // "M1"
DEVICE_PORT2 = 4;  // "M2"

// NEW:
DEVICE_PORT0 = 3;  // "M1" 
DEVICE_PORT1 = 4;  // "M2"
```

**Impact:** This is a **breaking change** that must be coordinated with firmware updates.

#### 2. New Fields Added
- `heartbeat_enabled` in NodeSettings
- Additional PID controllers (`cctrl_kp`, `cctrl_ki`, `cctrl_kd`) in SMAControllerSettings
- Raw sensor data (`vld_raw`, `curr_raw`) in SMAStatusDump


## Validation Impact

### **Enhanced CSV Output Format**

**Supply Voltage Validation:**
```csv
timestamp,node_id,supply_voltage,firmware_version,expected_voltage,load_condition,test_notes
1234567890.1,1.0.17,22.15,1.2.13,22.0,no_load,baseline test
```

**Muscle Measurement:**  
```csv
timestamp,node_id,muscle,load_amps,voltage_drop,resistance_mohms,enabled,firmware_version,supply_voltage,load_condition,test_notes
1234567890.1,1.0.17,0,0.1234,1.23,10.5,True,1.2.13,22.0,resistive_10ohm,calibration test
```

## Summary

This update aligns the Python library with the v1.1.1 firmware protocol capabilities, providing:

1. **Complete firmware version tracking** (X.X.X format)
2. **Enhanced validation metadata** for thorough sensor testing
3. **Protocol compatibility** with updated firmware versions
4. **Backward compatibility** for existing deployments

The changes enable more precise validation tracking and better correlation of measurement variations with specific firmware patch levels. 
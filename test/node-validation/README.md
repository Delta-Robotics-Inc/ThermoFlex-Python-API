# ThermoFlex Node Sensor Validation

This directory contains sensor validation scripts for ThermoFlex Nodes. The goal is to ensure that every controller reports consistent sensor values so that global voltage and current limits can be applied safely across multiple devices.

## Objectives

1. **Verify supply voltage consistency** - Ensure all nodes report the same supply voltage
2. **Measure no-load current baselines** - Compare idle current draw between nodes  
3. **Compare current pulse responses** - Check for calibration differences in current control

## Test Scripts

| Script | Purpose | Output |
|--------|---------|---------|
| `read_voltage.py` | Supply voltage validation | `voltage_readings.csv` |
| `no_load_current.py` | No-load current baseline | `no_load_current.csv` |
| `current_pulse.py` | Current control validation | `current_pulse.csv` |

## Quick Start

### 1. Supply Voltage Validation

Logs supply voltage for all detected nodes over a specified time interval:

```bash
python read_voltage.py --duration 10 --outfile voltages.csv
```

**Expected Results:** All nodes should report very similar supply voltage readings (within ~0.1V).

### 2. No-Load Current Measurement

Measures idle current with no loads attached to muscle ports:

```bash
python no_load_current.py --duration 10 --outfile idle_current.csv
```

**Expected Results:** Very low current readings (< 0.1A typically) that are consistent between nodes.

### 3. Current Pulse Test

Applies a current setpoint and records the response curve:

```bash
python current_pulse.py --target 2.5 --pulse 1.0 --duration 5 --outfile pulse.csv
```

**Safety Note:** Ensure the target current is safe for your connected loads. The script will prompt for confirmation before starting.

## Script Parameters

### Common Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--duration` | Total test duration in seconds | 10.0 |
| `--interval` | Sampling interval in seconds | 0.1 |
| `--outfile` | Output CSV filename | Script-specific |

### Current Pulse Specific

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--target` | Target current in amperes | 2.5 |
| `--pulse` | Pulse duration in seconds | 1.0 |

## CSV Output Format

### Voltage Readings (`voltage_readings.csv`)
```
timestamp,node_id,supply_voltage
1640995200.123,1.0.17,12.045
1640995200.223,1.0.17,12.043
```

### No-Load Current (`no_load_current.csv`)
```
timestamp,node_id,muscle,load_amps,enabled,voltage_drop
1640995200.123,1.0.17,0,0.0123,False,0.0
1640995200.123,1.0.17,1,0.0089,False,0.0
```

### Current Pulse (`current_pulse.csv`)
```
timestamp,node_id,muscle,load_amps,setpoint,enabled,phase
1640995200.123,1.0.17,0,0.012,0.0,False,baseline
1640995201.123,1.0.17,0,2.487,2.5,True,pulse
1640995202.123,1.0.17,0,0.015,0.0,False,recovery
```

## Data Analysis

### Excel/Spreadsheet Analysis

1. **Import CSV files** into Excel or your preferred spreadsheet application
2. **Create time-series plots** with separate lines/colors for each node
3. **Compare readings** to identify offsets or discrepancies

### Voltage Analysis
- Plot voltage vs time for all nodes
- Look for consistent readings across devices
- Typical tolerance: ±0.1V

### Current Analysis
- Compare no-load baselines between nodes
- Analyze pulse response curves for consistency
- Check rise times and steady-state accuracy

### Expected Results

| Test | Good Result | Investigation Needed |
|------|-------------|----------------------|
| **Voltage** | All nodes within ±0.1V | Voltage differences > 0.2V |
| **No-Load** | All currents < 0.1A, similar values | Large differences between nodes |
| **Pulse** | Consistent rise times and steady-state | Different response curves |

## Troubleshooting

### No Nodes Found
- Check USB connections
- Verify nodes are powered on  
- Try increasing discovery timeout: `--timeout 15`

### Poor Data Quality
- Reduce sampling interval: `--interval 0.2`
- Check for loose connections
- Ensure stable power supply

### Current Control Issues
- Verify loads are properly connected
- Check that muscle ports are functional
- Monitor for overheating during pulse tests

## Safety Considerations

### Current Pulse Testing
- ⚠️ **Start with low currents** (< 1A) to verify safe operation
- 🌡️ **Monitor temperature** - SMA actuators can get very hot
- 🔌 **Verify connections** before applying high currents  
- ⚡ **Use appropriate loads** rated for test currents
- 🛑 **Have emergency stop** ready if needed

### General Safety
- 👀 **Supervise all tests** - do not leave unattended
- 🧯 **Fire safety** - have extinguisher nearby for high-current tests
- 📏 **Respect limits** - stay within device current ratings
- 🔧 **Proper setup** - secure all connections before testing

## Requirements

- Python 3.7+
- ThermoFlex Python library
- Connected ThermoFlex node(s)
- USB or network connectivity

## Support

For issues with the validation scripts:
1. Check node connectivity and power
2. Verify latest ThermoFlex library version
3. Review CSV output for error entries
4. Check script debug output for specific errors

For calibration issues identified by validation:
1. Document the specific differences found
2. Note which nodes show deviations
3. Consider firmware calibration updates if needed 

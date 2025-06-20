#!/usr/bin/env python3
"""
No-Load Current Validation Script

This script measures the idle current of each muscle port with no load attached.
Part of the sensor validation test plan to verify current measurement consistency 
across ThermoFlex Nodes.

IMPORTANT TEST CONDITIONS:
- NO PHYSICAL LOAD should be connected to any muscle output terminals
- Test measures baseline current with muscle controller enabled but no external load
- For accurate no-load current measurement, muscles must be:
  1. Set to PWM (percent) mode
  2. Set to 0% setpoint (no PWM output)
  3. ENABLED (not disabled) - this is critical for current measurement accuracy

Usage:
    python no_load_current.py --duration 10 --outfile idle_current.csv

The CSV output contains:
- timestamp: Unix timestamp in seconds
- node_id: Node identifier (e.g., "1.0.17")
- muscle: Muscle port identifier (e.g., "0", "1")
- load_amps: Current reading in amperes
- enabled: Muscle enable status (should be True for proper no-load test)
- voltage_drop: Voltage drop measurement in volts

Import the CSV results from multiple devices into a spreadsheet and compare
current readings to identify any calibration offsets between nodes.
"""

import argparse
import csv
import os
import time
from datetime import datetime
import thermoflex as tf


def setup_muscle_for_no_load_measurement(muscle):
    """
    Set up a muscle for proper no-load current measurement.
    
    For accurate no-load current readings, the muscle must be enabled
    with a setpoint of 0 in PWM mode, not just disabled.
    
    Args:
        muscle: Muscle object to configure
        
    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        print(f"   Setting up muscle {muscle.get_port_number()} for no-load measurement...")
        
        # 1. Set to PWM (percent) mode
        muscle.setMode("percent")
        print(f"     ✓ Set to PWM mode")
        
        # 2. Set setpoint to 0% (no PWM output)
        muscle.setSetpoint(conmode="percent", setpoint=0.0)
        print(f"     ✓ Set setpoint to 0%")
        
        # 3. Enable the muscle (critical for accurate current measurement)
        muscle.setEnable(True)
        print(f"     ✓ Enabled muscle (required for accurate current measurement)")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Error setting up muscle {muscle.get_port_number()}: {e}")
        return False


def sample_current(nodes, duration=10.0, interval=0.1, outfile="no_load_current.csv"):
    """
    Sample no-load current from all muscle ports across multiple nodes
    
    Args:
        nodes: List of ThermoFlex node objects
        duration: Total sampling duration in seconds
        interval: Sampling interval in seconds
        outfile: Output CSV file path (timestamp will be added)
    """
    # Add timestamp to filename for uniqueness
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name, ext = os.path.splitext(outfile)
    timestamped_outfile = f"{base_name}_{timestamp_str}{ext}"
    
    start_time = time.time()
    sample_count = 0
    successful_samples = 0
    total_muscles = sum(len(node.muscles) for node in nodes)
    
    print(f"Starting no-load current sampling for {duration}s at {interval}s intervals...")
    print(f"Monitoring {len(nodes)} nodes with {total_muscles} total muscle ports")
    print(f"Output file: {os.path.abspath(timestamped_outfile)}")
    print()
    print("⚠️  CRITICAL: Ensure NO physical loads are connected to muscle output terminals!")
    print("   This test measures baseline current with controllers enabled but no external load.")
    print()
    
    # Set up all muscles for no-load measurement
    print("=== Setting up muscles for no-load measurement ===")
    setup_success_count = 0
    
    for node_idx, node in enumerate(nodes):
        node_id = ".".join(str(b) for b in node.id)
        print(f"Node {node_id}:")
        
        for muscle_key, muscle in node.muscles.items():
            if setup_muscle_for_no_load_measurement(muscle):
                setup_success_count += 1
            else:
                print(f"     ⚠️  Warning: Failed to set up muscle {muscle_key}")
    
    print(f"\n✅ Successfully configured {setup_success_count}/{total_muscles} muscles")
    
    # Wait for muscle controllers to stabilize
    print("Waiting 3 seconds for muscle controllers to stabilize...")
    time.sleep(3.0)
    
    print(f"\n=== Starting data capture ===")
    
    with open(timestamped_outfile, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        
        # CSV header
        writer.writerow(["timestamp", "node_id", "muscle", "load_amps", "enabled", "voltage_drop", "resistance_mohms"])
        csvfile.flush()
        
        while time.time() - start_time < duration:
            sample_start = time.time()
            sample_count += 1
            
            for node_idx, node in enumerate(nodes):
                try:
                    # Request status from all devices to get muscle data
                    node.status("compact", device='all')
                    time.sleep(0.05)  # Brief wait for response
                    
                    nid = ".".join(str(b) for b in node.id)
                    
                    for muscle_key, muscle in node.muscles.items():
                        try:
                            # Get readings using accessor methods
                            current = muscle.get_current()
                            voltage_drop = muscle.get_voltage_drop()
                            resistance = muscle.get_resistance()
                            enabled = muscle.is_enabled()
                            
                            timestamp = time.time()
                            
                            # Write data row
                            writer.writerow([timestamp, nid, muscle_key, current, enabled, voltage_drop, resistance])
                            csvfile.flush()
                            
                            if current is not None:
                                successful_samples += 1
                                status_str = "ENABLED" if enabled else "disabled"
                                print(f"Sample {sample_count:3d} - Node {nid} muscle {muscle_key}: {current:.4f}A ({status_str})")
                                
                                # Warn if muscle is not enabled (incorrect setup)
                                if not enabled:
                                    print(f"   ⚠️  WARNING: Muscle should be ENABLED for accurate no-load measurement!")
                            else:
                                print(f"Sample {sample_count:3d} - Node {nid} muscle {muscle_key}: No current data")
                                
                        except Exception as e:
                            print(f"Sample {sample_count:3d} - Error reading muscle {muscle_key} from node {nid}: {e}")
                            # Write error entry
                            writer.writerow([time.time(), nid, muscle_key, "ERROR", "ERROR", "ERROR", "ERROR"])
                            csvfile.flush()
                            
                except Exception as e:
                    print(f"Sample {sample_count:3d} - Error reading from node {node_idx}: {e}")
            
            # Maintain consistent sampling interval
            elapsed = time.time() - sample_start
            remaining = interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
            elif elapsed > interval * 1.5:
                print(f"⚠️  Warning: Sample took {elapsed:.3f}s (> {interval}s interval)")
    
    # Cleanup - disable all muscles for safety
    print(f"\n=== Cleanup - Disabling all muscles for safety ===")
    for node in nodes:
        try:
            node.disableAll()
            node_id = ".".join(str(b) for b in node.id)
            print(f"   ✓ Disabled all muscles on node {node_id}")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not disable muscles on node: {e}")
    
    # Summary
    total_expected = sample_count * total_muscles
    success_rate = (successful_samples / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\n=== No-Load Current Sampling Complete ===")
    print(f"Duration: {time.time() - start_time:.1f}s")
    print(f"Samples taken: {sample_count}")
    print(f"Successful readings: {successful_samples}/{total_expected} ({success_rate:.1f}%)")
    print(f"Output file: {os.path.abspath(timestamped_outfile)}")
    
    return timestamped_outfile


def main():
    parser = argparse.ArgumentParser(description='Measure no-load current for sensor validation')
    parser.add_argument('--duration', type=float, default=10.0,
                       help='Sampling duration in seconds (default: 10.0)')
    parser.add_argument('--interval', type=float, default=0.1,
                       help='Sample interval in seconds (default: 0.1)')
    parser.add_argument('--outfile', default='no_load_current.csv',
                       help='CSV output file base name (timestamp will be added, default: no_load_current.csv)')
    args = parser.parse_args()

    print("=== THERMOFLEX NO-LOAD CURRENT VALIDATION ===\n")
    print("CRITICAL TEST CONDITIONS:")
    print("• NO physical loads should be connected to muscle output terminals")
    print("• Test measures baseline current with muscle controllers enabled")
    print("• Controllers will be set to: PWM mode, 0% setpoint, ENABLED")
    print("• This setup provides accurate no-load current readings\n")

    try:
        # Discover nodes using modern API
        print("Discovering ThermoFlex networks...")
        
        # Try to get USB node first (most common case)
        try:
            node = tf.get_usb_node(timeout=10.0)
            node_list = [node]
            print(f"✅ Found USB node: {'.'.join(str(b) for b in node.id)}")
        except Exception:
            # Fallback to network discovery if USB method fails
            print("USB discovery failed, trying network discovery...")
            nets = tf.discover([105])  # PID 105 for ThermoFlex
            for net in nets:
                net.refreshDevices()
            time.sleep(2.0)  # Wait for device discovery
            node_list = [node for net in nets for node in net.node_list]

        if not node_list:
            print("❌ No ThermoFlex nodes found!")
            print("   - Check USB connections")
            print("   - Verify nodes are powered on")
            return 1

        print(f"✅ Found {len(node_list)} ThermoFlex node(s):")
        total_muscles = 0
        for i, node in enumerate(node_list):
            node_id = ".".join(str(b) for b in node.id)
            muscle_count = len(node.muscles)
            total_muscles += muscle_count
            print(f"   Node {i}: {node_id} ({muscle_count} muscles)")
        
        print(f"   Total muscle ports: {total_muscles}")
        
        # Validate arguments
        if args.interval < 0.05:
            print("⚠️  Warning: Very short interval may cause timing issues")
        
        if args.duration < 5.0:
            print("⚠️  Warning: Short duration may not provide enough data for baseline measurement")

        # Start current sampling
        output_file = sample_current(node_list, args.duration, args.interval, args.outfile)

        print(f"\n✅ No-load current validation data saved to: {output_file}")
        print("   Import this CSV into Excel/spreadsheet for analysis")
        print("   Plot current vs time with different colors for each node/muscle")
        print("   Compare baseline current levels to identify calibration differences")
        print("   Expected: Very low current readings (typically < 0.1A)")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        print("\nShutting down...")
        tf.endAll(timeout=5.0)


if __name__ == '__main__':
    exit(main())

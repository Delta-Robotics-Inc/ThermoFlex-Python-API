#!/usr/bin/env python3
"""
Muscle Current and Voltage Measurement Script

This script measures current and voltage from each muscle port under user-defined
load conditions. Part of the sensor validation test plan to verify measurement
consistency across ThermoFlex Nodes under various operating conditions.

TEST CONDITIONS:
- User defines supply voltage and load conditions via interactive prompts
- Script measures both current and voltage from all muscle ports
- Load conditions and test metadata are recorded in the CSV output
- No automatic muscle configuration - user maintains control of muscle settings

Usage:
    python muscle_measurement.py --duration 10 --outfile muscle_data.csv

The CSV output contains:
- timestamp: Unix timestamp in seconds
- node_id: Node identifier (e.g., "1.0.17")
- muscle: Muscle port identifier (e.g., "0", "1")
- load_amps: Current reading in amperes
- voltage_drop: Voltage drop measurement in volts
- resistance_mohms: Calculated resistance in milliohms
- enabled: Muscle enable status
- firmware_version: Node firmware version (e.g., "1.2")
- supply_voltage: User-specified supply voltage (metadata)
- load_condition: User-specified load condition (metadata)
- test_notes: Additional user notes (metadata)

Import the CSV results from multiple devices into a spreadsheet and compare
measurements to identify any calibration offsets between nodes.
"""

import argparse
import csv
import os
import time
from datetime import datetime
import thermoflex as tf


def get_test_metadata():
    """
    Collect test metadata from user via interactive prompts.
    
    Returns:
        dict: Dictionary containing test metadata
    """
    print("\n=== Test Configuration ===")
    print("Please provide the following test conditions for metadata recording:")
    
    # Get supply voltage
    while True:
        try:
            supply_voltage = input("Supply voltage (V): ").strip()
            if supply_voltage:
                float(supply_voltage)  # Validate it's a number
                break
            else:
                print("Please enter a valid supply voltage.")
        except ValueError:
            print("Please enter a valid numeric value for supply voltage.")
    
    # Get load condition
    load_condition = input("Load condition (e.g., 'no_load', 'resistive_10ohm', 'muscle_attached'): ").strip()
    if not load_condition:
        load_condition = "unspecified"
    
    # Get additional notes
    test_notes = input("Additional test notes (optional): ").strip()
    if not test_notes:
        test_notes = "none"
    
    metadata = {
        'supply_voltage': supply_voltage,
        'load_condition': load_condition,
        'test_notes': test_notes
    }
    
    print(f"\n✅ Test metadata recorded:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    
    return metadata


def sample_muscle_data(nodes, duration=10.0, interval=0.1, outfile="muscle_data.csv", metadata=None):
    """
    Sample current and voltage from all muscle ports across multiple nodes
    
    Args:
        nodes: List of ThermoFlex node objects
        duration: Total sampling duration in seconds
        interval: Sampling interval in seconds
        outfile: Output CSV file path (timestamp will be added)
        metadata: Dictionary containing test metadata
    """
    # Add timestamp to filename for uniqueness
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name, ext = os.path.splitext(outfile)
    timestamped_outfile = f"{base_name}_{timestamp_str}{ext}"
    
    start_time = time.time()
    sample_count = 0
    successful_samples = 0
    total_muscles = sum(len(node.muscles) for node in nodes)
    
    print(f"\nStarting muscle data sampling for {duration}s at {interval}s intervals...")
    print(f"Monitoring {len(nodes)} nodes with {total_muscles} total muscle ports")
    print(f"Output file: {os.path.abspath(timestamped_outfile)}")
    print()
    print("📋 User is responsible for muscle configuration and load setup")
    print("   Script will measure current and voltage from muscles as-is")
    print()
    
    # Wait for user confirmation
    input("Press Enter when ready to start data collection...")
    
    print(f"\n=== Starting data capture ===")
    
    with open(timestamped_outfile, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        
        # Write metadata header
        if metadata:
            writer.writerow(["# Test Metadata"])
            for key, value in metadata.items():
                writer.writerow([f"# {key}", value])
            writer.writerow(["# "])  # Separator
        
        # CSV data header
        writer.writerow(["timestamp", "node_id", "muscle", "load_amps", "voltage_drop", 
                        "resistance_mohms", "enabled", "firmware_version", "supply_voltage", "supply_voltage_raw", 
                        "voltage_load_raw", "current_raw", "load_condition", "test_notes"])
        csvfile.flush()
        
        while time.time() - start_time < duration:
            sample_start = time.time()
            sample_count += 1
            
            for node_idx, node in enumerate(nodes):
                try:
                    # Request status from all devices to get muscle data including raw values
                    node.status("dump", device='all')  # Use dump to get raw data
                    time.sleep(0.05)  # Brief wait for response
                    
                    # Get node info once per node
                    nid = ".".join(str(b) for b in node.id)
                    
                    # Get firmware version and supply voltage (already requested dump above)
                    try:
                        firmware_version = node.get_firmware_version()
                        supply_voltage = node.get_supply_voltage()
                        supply_voltage_raw = node.get_supply_voltage_raw()
                    except Exception:
                        firmware_version = "N/A"
                        supply_voltage = None
                        supply_voltage_raw = None
                    
                    for muscle_key, muscle in node.muscles.items():
                        try:
                            # Get readings using accessor methods (scaled values)
                            current = muscle.get_current()
                            voltage_drop = muscle.get_voltage_drop()
                            resistance = muscle.get_resistance()
                            enabled = muscle.is_enabled()
                            
                            # Get raw ADC readings (dump status only)
                            voltage_load_raw = muscle.get_voltage_load_raw()
                            current_raw = muscle.get_current_raw()
                            
                            timestamp = time.time()
                            
                            # Write data row with metadata including raw values
                            writer.writerow([
                                timestamp, nid, muscle_key, current, voltage_drop, resistance, enabled, firmware_version,
                                supply_voltage, supply_voltage_raw, voltage_load_raw, current_raw,
                                metadata.get('supply_voltage', 'N/A') if metadata else 'N/A',
                                metadata.get('load_condition', 'N/A') if metadata else 'N/A',
                                metadata.get('test_notes', 'N/A') if metadata else 'N/A'
                            ])
                            csvfile.flush()
                            
                            if current is not None and voltage_drop is not None:
                                successful_samples += 1
                                status_str = "ENABLED" if enabled else "disabled"
                                fw_str = f" FW:{firmware_version}" if firmware_version != "N/A" else ""
                                raw_str = f" (raw: V={voltage_load_raw}, I={current_raw})" if voltage_load_raw is not None and current_raw is not None else ""
                                print(f"Sample {sample_count:3d} - Node {nid}{fw_str} muscle {muscle_key}: "
                                      f"{current:.4f}A, {voltage_drop:.3f}V ({status_str}){raw_str}")
                            else:
                                print(f"Sample {sample_count:3d} - Node {nid} muscle {muscle_key}: No data")
                                
                        except Exception as e:
                            print(f"Sample {sample_count:3d} - Error reading muscle {muscle_key} from node {nid}: {e}")
                            # Write error entry
                            writer.writerow([
                                time.time(), nid, muscle_key, "ERROR", "ERROR", "ERROR", "ERROR", firmware_version,
                                "ERROR", "ERROR", "ERROR", "ERROR",  # supply_voltage, supply_voltage_raw, voltage_load_raw, current_raw
                                metadata.get('supply_voltage', 'N/A') if metadata else 'N/A',
                                metadata.get('load_condition', 'N/A') if metadata else 'N/A',
                                metadata.get('test_notes', 'N/A') if metadata else 'N/A'
                            ])
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
    
    # Summary
    total_expected = sample_count * total_muscles
    success_rate = (successful_samples / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\n=== Muscle Data Sampling Complete ===")
    print(f"Duration: {time.time() - start_time:.1f}s")
    print(f"Samples taken: {sample_count}")
    print(f"Successful readings: {successful_samples}/{total_expected} ({success_rate:.1f}%)")
    print(f"Output file: {os.path.abspath(timestamped_outfile)}")
    
    return timestamped_outfile


def main():
    parser = argparse.ArgumentParser(description='Measure muscle current and voltage for validation')
    parser.add_argument('--duration', type=float, default=10.0,
                       help='Sampling duration in seconds (default: 10.0)')
    parser.add_argument('--interval', type=float, default=0.1,
                       help='Sample interval in seconds (default: 0.1)')
    parser.add_argument('--outfile', default='muscle_data.csv',
                       help='CSV output file base name (timestamp will be added, default: muscle_data.csv)')
    args = parser.parse_args()

    print("=== THERMOFLEX MUSCLE MEASUREMENT VALIDATION ===\n")
    print("This script measures current and voltage from muscle ports under")
    print("user-defined load conditions for sensor validation testing.")
    print()
    print("MEASUREMENT CONDITIONS:")
    print("• User defines supply voltage and load conditions")
    print("• Script measures current, voltage, and resistance from all muscle ports")
    print("• User is responsible for muscle configuration and load setup")
    print("• Test metadata is recorded in CSV for analysis")

    try:
        # Get test metadata from user
        metadata = get_test_metadata()

        # Discover nodes using modern API
        print("\nDiscovering ThermoFlex networks...")
        
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
            print("⚠️  Warning: Short duration may not provide enough data for analysis")

        # Start measurement sampling
        output_file = sample_muscle_data(node_list, args.duration, args.interval, args.outfile, metadata)

        print(f"\n✅ Muscle measurement data saved to: {output_file}")
        print("   Import this CSV into Excel/spreadsheet for analysis")
        print("   Plot current and voltage vs time with different colors for each node/muscle")
        print("   Compare measurements across nodes to identify calibration differences")
        print("   Test metadata is included in CSV header for reference")

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
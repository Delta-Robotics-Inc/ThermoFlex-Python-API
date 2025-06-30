#!/usr/bin/env python3
"""
Supply Voltage Validation Script

This script validates consistent supply voltage readings across ThermoFlex Nodes
under user-defined test conditions. Part of the sensor validation test plan to 
verify that supply voltage measurements are consistent and accurate across multiple
nodes when operating under the same supply conditions.

TEST CONDITIONS:
- User defines actual supply voltage and load conditions via interactive prompts
- Script measures supply voltage from all nodes for comparison
- Test metadata is recorded in CSV for analysis and validation reference

Usage:
    python val_supply_voltage.py --duration 10 --outfile supply_voltage_validation.csv

The CSV output contains:
- timestamp: Unix timestamp in seconds
- node_id: Node identifier (e.g., "1.0.17")  
- supply_voltage: Supply voltage reading in volts
- firmware_version: Node firmware version (e.g., "1.2")
- expected_voltage: User-specified actual supply voltage (metadata)
- load_condition: User-specified load condition (metadata)
- test_notes: Additional user notes (metadata)

Import the CSV results from multiple devices into a spreadsheet and plot the recorded 
curves with separate colors for each Node to identify any calibration offsets or 
measurement discrepancies against the expected voltage.
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
    print("Please provide the following test conditions for validation metadata:")
    
    # Get expected supply voltage
    while True:
        try:
            expected_voltage = input("Actual supply voltage (V): ").strip()
            if expected_voltage:
                float(expected_voltage)  # Validate it's a number
                break
            else:
                print("Please enter a valid supply voltage.")
        except ValueError:
            print("Please enter a valid numeric value for supply voltage.")
    
    # Get load condition
    load_condition = input("Load condition (e.g., 'no_load', 'loaded', 'mixed_load'): ").strip()
    if not load_condition:
        load_condition = "unspecified"
    
    # Get additional notes
    test_notes = input("Additional test notes (optional): ").strip()
    if not test_notes:
        test_notes = "none"
    
    metadata = {
        'expected_voltage': expected_voltage,
        'load_condition': load_condition,
        'test_notes': test_notes
    }
    
    print(f"\n✅ Test metadata recorded:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    
    return metadata


def sample_voltage(nodes, duration=10.0, interval=0.1, out_file="./voltage_readings.csv", metadata=None):
    """
    Sample supply voltage from multiple nodes over time with validation metadata
    
    Args:
        nodes: List of ThermoFlex node objects
        duration: Total sampling duration in seconds
        interval: Sampling interval in seconds  
        out_file: Output CSV file path (timestamp will be added)
        metadata: Dictionary containing test metadata
    """
    # Add timestamp to filename for uniqueness
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name, ext = os.path.splitext(out_file)
    timestamped_outfile = f"{base_name}_{timestamp_str}{ext}"
    
    start_time = time.time()
    sample_count = 0
    successful_samples = 0
    
    print(f"\nStarting voltage validation sampling for {duration}s at {interval}s intervals...")
    print(f"Monitoring {len(nodes)} nodes")
    print(f"Output file: {os.path.abspath(timestamped_outfile)}")
    
    # Wait for user confirmation
    input("\nPress Enter when ready to start voltage validation data collection...")
    
    with open(timestamped_outfile, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        print(f"\n=== Starting data capture ===")
        
        # Write metadata header
        if metadata:
            writer.writerow(["# Test Metadata"])
            for key, value in metadata.items():
                writer.writerow([f"# {key}", value])
            writer.writerow(["# "])  # Separator
        
        # CSV data header
        writer.writerow(["timestamp", "node_id", "supply_voltage", "supply_voltage_raw", "firmware_version", "expected_voltage", "load_condition", "test_notes"])
        csvfile.flush()
        
        while time.time() - start_time < duration:
            sample_start = time.time()
            sample_count += 1
            
            for node_idx, node in enumerate(nodes):
                try:
                    # Request status dump to get both voltage and firmware version
                    node.status("dump", device='node')
                    time.sleep(0.05)  # Brief wait for response
                    
                    # Get readings using accessor methods
                    v_supply = node.get_supply_voltage()
                    v_supply_raw = node.get_supply_voltage_raw()
                    firmware_version = node.get_firmware_version()
                    nid = node.get_node_id_string()
                    timestamp = time.time()
                    
                    # Validate data before writing
                    if v_supply is not None and nid:
                        writer.writerow([
                            timestamp, nid, v_supply, v_supply_raw, firmware_version,
                            metadata.get('expected_voltage', 'N/A') if metadata else 'N/A',
                            metadata.get('load_condition', 'N/A') if metadata else 'N/A',
                            metadata.get('test_notes', 'N/A') if metadata else 'N/A'
                        ])
                        csvfile.flush()
                        successful_samples += 1
                        expected_v = metadata.get('expected_voltage', 'N/A') if metadata else 'N/A'
                        fw_str = f" (FW: {firmware_version})" if firmware_version else ""
                        print(f"Sample {sample_count} - Node {nid}: {v_supply:.3f}V (expected: {expected_v}V){fw_str}")
                    else:
                        print(f"Sample {sample_count} - Node {nid}: Invalid voltage data ({v_supply})")
                        
                except Exception as e:
                    print(f"Sample {sample_count} - Error reading from node {node_idx}: {e}")
            
            # Maintain consistent sampling interval
            elapsed = time.time() - sample_start
            remaining = interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
            elif elapsed > interval * 1.5:  # Warn if significantly over interval
                print(f"Warning: Sample took {elapsed:.3f}s (> {interval}s interval)")
    
    # Summary
    total_expected = sample_count * len(nodes)
    success_rate = (successful_samples / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\n=== Voltage Validation Sampling Complete ===")
    print(f"Duration: {time.time() - start_time:.1f}s")
    print(f"Samples taken: {sample_count}")
    print(f"Successful readings: {successful_samples}/{total_expected} ({success_rate:.1f}%)")
    print(f"Output file: {os.path.abspath(timestamped_outfile)}")
    
    return timestamped_outfile


def main():
    parser = argparse.ArgumentParser(description='Validate supply voltage consistency for sensor validation')
    parser.add_argument('--duration', type=float, default=10.0, 
                       help='Validation duration in seconds (default: 10.0)')
    parser.add_argument('--interval', type=float, default=0.1, 
                       help='Sample interval in seconds (default: 0.1)')
    parser.add_argument('--outfile', default='supply_voltage_validation.csv', 
                       help='CSV output file base name (timestamp will be added, default: supply_voltage_validation.csv)')
    args = parser.parse_args()

    print("=== THERMOFLEX SUPPLY VOLTAGE VALIDATION ===\n")
    print("This script validates consistent supply voltage readings across")
    print("ThermoFlex Nodes under user-defined test conditions.")
    print()
    print("VALIDATION CONDITIONS:")
    print("• User defines actual supply voltage for comparison reference")
    print("• User defines load conditions for test documentation")
    print("• Script measures supply voltage from all nodes for comparison")
    print("• Test metadata is recorded in CSV for validation analysis")
    
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
            print("   - Try increasing discovery timeout")
            return 1
        
        print(f"✅ Found {len(node_list)} ThermoFlex node(s):")
        for i, node in enumerate(node_list):
            node_id = ".".join(str(b) for b in node.id)
            print(f"   Node {i}: {node_id}")
        
        # Validate arguments
        if args.interval < 0.05:
            print("⚠️  Warning: Very short interval may cause timing issues")
        
        if args.duration < 1.0:
            print("⚠️  Warning: Very short duration may not provide enough data")
        
        # Start voltage validation sampling
        output_file = sample_voltage(node_list, args.duration, args.interval, args.outfile, metadata)
        
        print(f"\n✅ Voltage validation data saved to: {output_file}")
        print("   Import this CSV into Excel/spreadsheet for analysis")
        print("   Plot voltage vs time with different colors for each node")
        print("   Compare measured voltages against expected voltage for calibration validation")
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

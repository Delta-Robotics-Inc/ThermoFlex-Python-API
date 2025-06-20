#!/usr/bin/env python3
"""
Supply Voltage Validation Script

This script logs supply voltage for all detected ThermoFlex Nodes over a user-defined 
time interval. Part of the sensor validation test plan to verify that supply voltage 
measurements are consistent across Nodes.

Usage:
    python read_voltage.py --duration 10 --outfile voltages.csv

The CSV output contains:
- timestamp: Unix timestamp in seconds
- node_id: Node identifier (e.g., "1.0.17")  
- supply_voltage: Supply voltage reading in volts

Import the CSV results from multiple devices into a spreadsheet and plot the recorded 
curves with separate colors for each Node to identify any offsets or discrepancies.
"""

import argparse
import csv
import os
import time
import thermoflex as tf


def sample_voltage(nodes, duration=10.0, interval=0.1, out_file="./voltage_readings.csv"):
    """
    Sample supply voltage from multiple nodes over time
    
    Args:
        nodes: List of ThermoFlex node objects
        duration: Total sampling duration in seconds
        interval: Sampling interval in seconds  
        out_file: Output CSV file path
    """
    start_time = time.time()
    sample_count = 0
    successful_samples = 0
    
    print(f"Starting voltage sampling for {duration}s at {interval}s intervals...")
    print(f"Monitoring {len(nodes)} nodes")
    
    with open(out_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        print(f"Writing to file: {os.path.abspath(out_file)}")
        
        # CSV header
        writer.writerow(["timestamp", "node_id", "supply_voltage"])
        csvfile.flush()
        
        while time.time() - start_time < duration:
            sample_start = time.time()
            sample_count += 1
            
            for node_idx, node in enumerate(nodes):
                try:
                    # Request status from node only (more efficient for voltage reading)
                    node.status("compact", device='node')
                    time.sleep(0.05)  # Brief wait for response
                    
                    # Get supply voltage using protocol-compliant field name
                    v_supply = node.node_status.get("v_supply")  # Protocol: v_supply
                    nid = ".".join(str(b) for b in node.id)
                    timestamp = time.time()
                    
                    # Validate data before writing
                    if v_supply is not None and nid:
                        writer.writerow([timestamp, nid, v_supply])
                        csvfile.flush()
                        successful_samples += 1
                        print(f"Sample {sample_count} - Node {nid}: {v_supply:.3f}V")
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
    
    print(f"\n=== Voltage Sampling Complete ===")
    print(f"Duration: {time.time() - start_time:.1f}s")
    print(f"Samples taken: {sample_count}")
    print(f"Successful readings: {successful_samples}/{total_expected} ({success_rate:.1f}%)")
    print(f"Output file: {os.path.abspath(out_file)}")


def main():
    parser = argparse.ArgumentParser(description='Log supply voltage for sensor validation')
    parser.add_argument('--duration', type=float, default=10.0, 
                       help='Logging duration in seconds (default: 10.0)')
    parser.add_argument('--interval', type=float, default=0.1, 
                       help='Sample interval in seconds (default: 0.1)')
    parser.add_argument('--outfile', default='voltage_readings.csv', 
                       help='CSV output file (default: voltage_readings.csv)')
    args = parser.parse_args()

    print("=== THERMOFLEX SUPPLY VOLTAGE VALIDATION ===\n")
    
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
        
        # Start voltage sampling
        sample_voltage(node_list, args.duration, args.interval, args.outfile)
        
        print(f"\n✅ Voltage validation data saved to: {args.outfile}")
        print("   Import this CSV into Excel/spreadsheet for analysis")
        print("   Plot voltage vs time with different colors for each node")
        print("   Look for consistent readings across all nodes")
        
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

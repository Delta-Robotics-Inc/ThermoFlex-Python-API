#!/usr/bin/env python3
"""
No-Load Current Validation Script

This script measures the idle current of each muscle port with no load attached.
Part of the sensor validation test plan to verify current measurement consistency 
across ThermoFlex Nodes.

Usage:
    python no_load_current.py --duration 10 --outfile idle_current.csv

The CSV output contains:
- timestamp: Unix timestamp in seconds
- node_id: Node identifier (e.g., "1.0.17")
- muscle: Muscle port identifier (e.g., "0", "1")
- load_amps: Current reading in amperes
- enabled: Muscle enable status (should be False for no-load test)

Import the CSV results from multiple devices into a spreadsheet and compare
current readings to identify any calibration offsets between nodes.
"""

import argparse
import csv
import os
import time
import thermoflex as tf


def sample_current(nodes, duration=10.0, interval=0.1, outfile="no_load_current.csv"):
    """
    Sample no-load current from all muscle ports across multiple nodes
    
    Args:
        nodes: List of ThermoFlex node objects
        duration: Total sampling duration in seconds
        interval: Sampling interval in seconds
        outfile: Output CSV file path
    """
    start_time = time.time()
    sample_count = 0
    successful_samples = 0
    total_muscles = sum(len(node.muscles) for node in nodes)
    
    print(f"Starting no-load current sampling for {duration}s at {interval}s intervals...")
    print(f"Monitoring {len(nodes)} nodes with {total_muscles} total muscle ports")
    print("⚠️  Ensure no loads are attached to muscle ports for accurate baseline readings")
    
    with open(outfile, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        print(f"Writing to file: {os.path.abspath(outfile)}")
        
        # CSV header with protocol-compliant field names
        writer.writerow(["timestamp", "node_id", "muscle", "load_amps", "enabled", "voltage_drop"])
        csvfile.flush()
        
        while time.time() - start_time < duration:
            sample_start = time.time()
            sample_count += 1
            
            for node_idx, node in enumerate(nodes):
                try:
                    # Request status from all devices to get muscle data
                    node.status("compact", device='all')
                    time.sleep(0.1)  # Wait for response
                    
                    nid = ".".join(str(b) for b in node.id)
                    
                    for muscle_key, muscle in node.muscles.items():
                        try:
                            # Get current reading using protocol-compliant field names
                            load_amps_data = muscle.SMA_status.get('load_amps', [])
                            load_vdrop_data = muscle.SMA_status.get('load_vdrop', [])
                            enabled = muscle.SMA_status.get('enabled', False)
                            
                            # Handle list vs direct value
                            if isinstance(load_amps_data, list) and load_amps_data:
                                current = load_amps_data[0]  # Most recent reading
                            else:
                                current = load_amps_data if load_amps_data is not None else None
                            
                            if isinstance(load_vdrop_data, list) and load_vdrop_data:
                                voltage = load_vdrop_data[0]
                            else:
                                voltage = load_vdrop_data if load_vdrop_data is not None else None
                            
                            timestamp = time.time()
                            
                            # Write data (even if None for tracking)
                            writer.writerow([timestamp, nid, muscle_key, current, enabled, voltage])
                            csvfile.flush()
                            
                            if current is not None:
                                successful_samples += 1
                                status_str = "ENABLED" if enabled else "disabled"
                                print(f"Sample {sample_count} - Node {nid} muscle {muscle_key}: {current:.4f}A ({status_str})")
                                
                                # Warn if muscle is enabled (should be disabled for no-load test)
                                if enabled:
                                    print(f"   ⚠️  WARNING: Muscle is enabled - may not be true no-load reading")
                            else:
                                print(f"Sample {sample_count} - Node {nid} muscle {muscle_key}: No data")
                                
                        except Exception as e:
                            print(f"Sample {sample_count} - Error reading muscle {muscle_key} from node {nid}: {e}")
                            # Write error entry
                            writer.writerow([time.time(), nid, muscle_key, "ERROR", "ERROR", "ERROR"])
                            csvfile.flush()
                            
                except Exception as e:
                    print(f"Sample {sample_count} - Error reading from node {node_idx}: {e}")
            
            # Maintain consistent sampling interval
            elapsed = time.time() - sample_start
            remaining = interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
            elif elapsed > interval * 1.5:
                print(f"Warning: Sample took {elapsed:.3f}s (> {interval}s interval)")
    
    # Summary
    total_expected = sample_count * total_muscles
    success_rate = (successful_samples / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\n=== No-Load Current Sampling Complete ===")
    print(f"Duration: {time.time() - start_time:.1f}s")
    print(f"Samples taken: {sample_count}")
    print(f"Successful readings: {successful_samples}/{total_expected} ({success_rate:.1f}%)")
    print(f"Output file: {os.path.abspath(outfile)}")


def main():
    parser = argparse.ArgumentParser(description='Measure no-load current for sensor validation')
    parser.add_argument('--duration', type=float, default=10.0,
                       help='Sampling duration in seconds (default: 10.0)')
    parser.add_argument('--interval', type=float, default=0.1,
                       help='Sample interval in seconds (default: 0.1)')
    parser.add_argument('--outfile', default='no_load_current.csv',
                       help='CSV output file (default: no_load_current.csv)')
    args = parser.parse_args()

    print("=== THERMOFLEX NO-LOAD CURRENT VALIDATION ===\n")

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
        
        # Safety check - ensure all muscles are disabled
        print("\nSafety check - ensuring all muscles are disabled...")
        for node in node_list:
            try:
                node.disableAll()
                print(f"   Disabled all muscles on node {'.'.join(str(b) for b in node.id)}")
            except Exception as e:
                print(f"   Warning: Could not disable muscles on node: {e}")
        
        time.sleep(1.0)  # Wait for disable commands to take effect
        
        # Validate arguments
        if args.interval < 0.05:
            print("⚠️  Warning: Very short interval may cause timing issues")
        
        if args.duration < 5.0:
            print("⚠️  Warning: Short duration may not provide enough data for baseline measurement")

        # Start current sampling
        sample_current(node_list, args.duration, args.interval, args.outfile)

        print(f"\n✅ No-load current validation data saved to: {args.outfile}")
        print("   Import this CSV into Excel/spreadsheet for analysis")
        print("   Plot current vs time with different colors for each node")
        print("   Compare baseline current levels to identify calibration differences")
        print("   Expected: Very low current readings (< 0.1A typically)")

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

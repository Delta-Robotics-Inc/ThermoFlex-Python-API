#!/usr/bin/env python3
"""
Current Pulse Validation Script

This script applies a configurable current setpoint and records the resulting current 
curve. Part of the sensor validation test plan to compare current pulse responses 
between ThermoFlex Nodes to check for calibration issues.

Usage:
    python current_pulse.py --target 2.5 --pulse 1.0 --duration 5 --outfile pulse.csv

The CSV output contains:
- timestamp: Unix timestamp in seconds
- node_id: Node identifier (e.g., "1.0.17")
- muscle: Muscle port identifier (e.g., "0", "1")
- load_amps: Current reading in amperes
- setpoint: Applied current setpoint in amperes
- enabled: Muscle enable status
- phase: Test phase ("baseline", "pulse", "recovery")

Import the CSV results from multiple devices into a spreadsheet and plot the recorded 
curves with separate colors for each Node to identify calibration differences.
"""

import argparse
import csv
import os
import time
import thermoflex as tf


def current_pulse_test(nodes, target_current=2.5, pulse_duration=1.0, total_duration=5.0, 
                      interval=0.1, outfile="current_pulse.csv"):
    """
    Perform current pulse test across multiple nodes
    
    Args:
        nodes: List of ThermoFlex node objects
        target_current: Target current in amperes for pulse
        pulse_duration: Duration of current pulse in seconds
        total_duration: Total test duration in seconds
        interval: Sampling interval in seconds
        outfile: Output CSV file path
    """
    print(f"=== CURRENT PULSE TEST ===")
    print(f"Target current: {target_current}A")
    print(f"Pulse duration: {pulse_duration}s")
    print(f"Total duration: {total_duration}s")
    print(f"Sampling interval: {interval}s")
    
    if pulse_duration >= total_duration:
        print("❌ Error: Pulse duration must be less than total duration")
        return False
    
    start_time = time.time()
    sample_count = 0
    successful_samples = 0
    total_muscles = sum(len(node.muscles) for node in nodes)
    
    # Test phases
    baseline_duration = 1.0  # 1 second baseline
    pulse_start_time = baseline_duration
    pulse_end_time = pulse_start_time + pulse_duration
    
    print(f"\nTest phases:")
    print(f"  0.0 - {baseline_duration:.1f}s: Baseline (disabled)")
    print(f"  {pulse_start_time:.1f} - {pulse_end_time:.1f}s: Pulse ({target_current}A)")
    print(f"  {pulse_end_time:.1f} - {total_duration:.1f}s: Recovery (disabled)")
    
    with open(outfile, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        print(f"\nWriting to file: {os.path.abspath(outfile)}")
        
        # CSV header
        writer.writerow(["timestamp", "node_id", "muscle", "load_amps", "setpoint", "enabled", "phase"])
        csvfile.flush()
        
        # Ensure all muscles start disabled
        print("\nInitializing - disabling all muscles...")
        for node in nodes:
            try:
                node.disableAll()
                # Set to current control mode for all muscles
                for muscle in node.muscles.values():
                    muscle.setMode("amps")
                    muscle.setSetpoint(conmode="amps", setpoint=target_current)
            except Exception as e:
                print(f"Warning: Error initializing node {'.'.join(str(b) for b in node.id)}: {e}")
        
        time.sleep(1.0)  # Wait for initialization
        print("Starting pulse test...")
        
        while time.time() - start_time < total_duration:
            sample_start = time.time()
            elapsed = sample_start - start_time
            sample_count += 1
            
            # Determine current phase
            if elapsed < pulse_start_time:
                phase = "baseline"
                should_enable = False
            elif elapsed < pulse_end_time:
                phase = "pulse"
                should_enable = True
            else:
                phase = "recovery"
                should_enable = False
            
            # Control muscle enable state based on phase
            for node in nodes:
                try:
                    for muscle in node.muscles.values():
                        current_enabled = muscle.SMA_status.get('enabled', False)
                        if should_enable and not current_enabled:
                            muscle.setEnable(True)
                        elif not should_enable and current_enabled:
                            muscle.setEnable(False)
                except Exception as e:
                    pass  # Continue sampling even if control fails
            
            # Sample current from all nodes
            for node_idx, node in enumerate(nodes):
                try:
                    # Request status from all devices
                    node.status("compact", device='all')
                    time.sleep(0.05)  # Brief wait for response
                    
                    nid = ".".join(str(b) for b in node.id)
                    
                    for muscle_key, muscle in node.muscles.items():
                        try:
                            # Get readings using protocol-compliant field names
                            load_amps_data = muscle.SMA_status.get('load_amps', [])
                            enabled = muscle.SMA_status.get('enabled', False)
                            setpoint = muscle.SMA_status.get('setpoint')
                            
                            # Handle list vs direct value for current
                            if isinstance(load_amps_data, list) and load_amps_data:
                                current = load_amps_data[0]
                            else:
                                current = load_amps_data if load_amps_data is not None else None
                            
                            # Use target current as setpoint if firmware setpoint is garbage
                            if setpoint is None or abs(setpoint) > 100.0:
                                setpoint = target_current if should_enable else 0.0
                            
                            timestamp = time.time()
                            
                            # Write data
                            writer.writerow([timestamp, nid, muscle_key, current, setpoint, enabled, phase])
                            csvfile.flush()
                            
                            if current is not None:
                                successful_samples += 1
                                status = "ON" if enabled else "OFF"
                                print(f"T+{elapsed:.1f}s [{phase:8}] Node {nid} M{muscle_key}: {current:.3f}A ({status})")
                            
                        except Exception as e:
                            # Write error entry
                            writer.writerow([time.time(), nid, muscle_key, "ERROR", target_current, "ERROR", phase])
                            csvfile.flush()
                            
                except Exception as e:
                    print(f"Sample {sample_count} - Error reading from node {node_idx}: {e}")
            
            # Maintain consistent sampling interval
            elapsed_sample = time.time() - sample_start
            remaining = interval - elapsed_sample
            if remaining > 0:
                time.sleep(remaining)
        
        # Ensure all muscles are disabled at end
        print("\nTest complete - disabling all muscles...")
        for node in nodes:
            try:
                node.disableAll()
            except Exception as e:
                print(f"Warning: Error disabling muscles: {e}")
    
    # Summary
    total_expected = sample_count * total_muscles
    success_rate = (successful_samples / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\n=== Current Pulse Test Complete ===")
    print(f"Duration: {time.time() - start_time:.1f}s")
    print(f"Samples taken: {sample_count}")
    print(f"Successful readings: {successful_samples}/{total_expected} ({success_rate:.1f}%)")
    print(f"Output file: {os.path.abspath(outfile)}")
    
    return success_rate > 50  # Consider successful if >50% readings obtained


def main():
    parser = argparse.ArgumentParser(description='Current pulse validation test')
    parser.add_argument('--target', type=float, default=2.5,
                       help='Target current in amperes (default: 2.5)')
    parser.add_argument('--pulse', type=float, default=1.0,
                       help='Pulse duration in seconds (default: 1.0)')
    parser.add_argument('--duration', type=float, default=5.0,
                       help='Total test duration in seconds (default: 5.0)')
    parser.add_argument('--interval', type=float, default=0.1,
                       help='Sampling interval in seconds (default: 0.1)')
    parser.add_argument('--outfile', default='current_pulse.csv',
                       help='CSV output file (default: current_pulse.csv)')
    args = parser.parse_args()

    print("=== THERMOFLEX CURRENT PULSE VALIDATION ===\n")

    # Validate arguments
    if args.target <= 0 or args.target > 10:
        print("❌ Error: Target current must be between 0 and 10 amperes")
        return 1
    
    if args.pulse <= 0 or args.pulse >= args.duration:
        print("❌ Error: Pulse duration must be positive and less than total duration")
        return 1
    
    if args.interval < 0.05:
        print("⚠️  Warning: Very short interval may cause timing issues")

    try:
        # Discover nodes
        print("Discovering ThermoFlex networks...")
        
        try:
            node = tf.get_usb_node(timeout=10.0)
            node_list = [node]
            print(f"✅ Found USB node: {'.'.join(str(b) for b in node.id)}")
        except Exception:
            print("USB discovery failed, trying network discovery...")
            nets = tf.discover([105])
            for net in nets:
                net.refreshDevices()
            time.sleep(2.0)
            node_list = [node for net in nets for node in net.node_list]

        if not node_list:
            print("❌ No ThermoFlex nodes found!")
            return 1

        print(f"✅ Found {len(node_list)} ThermoFlex node(s):")
        total_muscles = 0
        for i, node in enumerate(node_list):
            node_id = ".".join(str(b) for b in node.id)
            muscle_count = len(node.muscles)
            total_muscles += muscle_count
            print(f"   Node {i}: {node_id} ({muscle_count} muscles)")

        print(f"   Total muscle ports: {total_muscles}")
        
        # Safety warnings
        print(f"\n⚠️  SAFETY WARNINGS:")
        print(f"   - Target current: {args.target}A - ensure this is safe for your setup")
        print(f"   - Ensure proper heat dissipation for connected loads")
        print(f"   - Monitor for overheating during test")
        print(f"   - Test will run for {args.duration}s total")
        
        # Confirm before proceeding
        try:
            confirm = input("\nProceed with current pulse test? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Test cancelled by user")
                return 0
        except KeyboardInterrupt:
            print("\nTest cancelled by user")
            return 0

        # Run the test
        success = current_pulse_test(
            node_list, 
            target_current=args.target,
            pulse_duration=args.pulse,
            total_duration=args.duration,
            interval=args.interval,
            outfile=args.outfile
        )

        print(f"\n✅ Current pulse validation data saved to: {args.outfile}")
        print("   Import this CSV into Excel/spreadsheet for analysis")
        print("   Plot current vs time with different colors for each node")
        print("   Compare pulse response curves to identify calibration differences")
        print("   Look for consistent rise times and steady-state values")

        return 0 if success else 1

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
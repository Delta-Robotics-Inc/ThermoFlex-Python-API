"""
FIXED VERSION of current_pulse.py

Key fixes:
1. Proper timing for status updates
2. Correct data structure handling for load_amps
3. Better error handling and data validation
4. More efficient status polling
5. Enhanced debugging output
"""

import argparse
import csv
import os
import time
import thermoflex as tf


def sample_current(nodes, duration=10.0, interval=0.5, outfile="no_load_current.csv"):
    """
    Sample current readings from nodes with improved timing and error handling
    
    Args:
        nodes: List of node objects
        duration: Total sampling duration in seconds
        interval: Interval between samples (minimum 0.5s recommended for reliable readings)
        outfile: Output CSV file name
    """
    start = time.time()
    sample_count = 0
    successful_readings = 0
    
    with open(outfile, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        print("Writing to file: ", os.path.abspath(outfile))
        writer.writerow(["timestamp", "node_id", "muscle", "load_amps", "load_voltdrop", "enable_status"])
        csvfile.flush()  # Ensure header is written immediately
        
        # Initial status request for all nodes
        print("Requesting initial status from all nodes...")
        for node in nodes:
            try:
                node.status("compact")
            except Exception as e:
                print(f"Error requesting status from node: {e}")
        
        # Wait for initial status responses
        time.sleep(1.0)
        
        while time.time() - start < duration:
            sample_start = time.time()
            sample_count += 1
            
            print(f"\n--- Sample {sample_count} at {time.time() - start:.1f}s ---")
            
            for node_idx, node in enumerate(nodes):
                try:
                    # Request fresh status (but don't wait for it immediately)
                    node.status("compact")
                    
                    # Give some time for status response to arrive
                    time.sleep(0.2)
                    
                    nid = ".".join(str(b) for b in node.id)
                    
                    for key, muscle in node.muscles.items():
                        try:
                            # Check if we have recent data
                            load_amps_data = muscle.SMA_status.get('load_amps', [])
                            load_voltdrop_data = muscle.SMA_status.get('load_voltdrop', [])
                            enable_status = muscle.enable_status
                            
                            # Handle the data structure correctly
                            # CRITICAL FIX: load_amps is a LIST, not a direct value
                            if isinstance(load_amps_data, list) and load_amps_data:
                                # Get most recent reading (first element in list)
                                amps = load_amps_data[0]
                            else:
                                # Direct value or empty list
                                amps = load_amps_data if load_amps_data else None
                            
                            if isinstance(load_voltdrop_data, list) and load_voltdrop_data:
                                voltage = load_voltdrop_data[0]
                            else:
                                voltage = load_voltdrop_data if load_voltdrop_data else None
                            
                            # Validate and write data
                            if nid and key is not None:
                                writer.writerow([time.time(), nid, key, amps, voltage, enable_status])
                                csvfile.flush()  # Flush after each write
                                
                                if amps is not None:
                                    successful_readings += 1
                                    print(f"  Node {nid} muscle {key}: {amps:.4f}A, {voltage:.4f}V, enabled: {enable_status}")
                                else:
                                    print(f"  Node {nid} muscle {key}: No current data available")
                            else:
                                print(f"  Warning: Invalid data for node {nid}, muscle {key}")
                                
                        except Exception as e:
                            print(f"  Error reading muscle {key} from node {nid}: {e}")
                            # Write error entry
                            writer.writerow([time.time(), nid, key, "ERROR", "ERROR", "ERROR"])
                            csvfile.flush()
                            
                except Exception as e:
                    print(f"Error processing node {node_idx}: {e}")
            
            # Maintain consistent sampling interval
            elapsed = time.time() - sample_start
            remaining_interval = interval - elapsed
            if remaining_interval > 0:
                time.sleep(remaining_interval)
            else:
                print(f"Warning: Sample took {elapsed:.2f}s, longer than {interval}s interval")
    
    print(f"\nSampling completed!")
    print(f"Total samples: {sample_count}")
    print(f"Successful current readings: {successful_readings}")
    if sample_count > 0 and nodes:
        expected_readings = sample_count * len(nodes) * len(nodes[0].muscles)
        print(f"Success rate: {successful_readings/expected_readings*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(description='Measure no-load current (FIXED VERSION)')
    parser.add_argument('--duration', type=float, default=10.0, help='Sampling duration in seconds')
    parser.add_argument('--interval', type=float, default=0.5, help='Sampling interval in seconds (min 0.5s recommended)')
    parser.add_argument('--outfile', default='no_load_current_fixed.csv', help='Output CSV file')
    args = parser.parse_args()

    # Validate arguments
    if args.interval < 0.2:
        print("Warning: Interval < 0.2s may cause timing issues. Consider using 0.5s or higher.")
    
    try:
        print("Discovering Thermoflex networks...")
        nets = tf.discover([105])
        
        print("Refreshing devices...")
        for net in nets:
            net.refreshDevices()
        
        # Wait for device discovery - CRITICAL: Give time for devices to respond
        print("Waiting for device discovery...")
        time.sleep(2.0)
        
        node_list = [node for net in nets for node in net.node_list]
        
        if not node_list:
            print("Error: No nodes found!")
            print("Make sure:")
            print("1. Hardware is connected via USB")
            print("2. Drivers are installed")
            print("3. No other software is using the serial port")
            return
        
        print(f"Found {len(node_list)} nodes")
        
        # Show node information
        for i, node in enumerate(node_list):
            nid = ".".join(str(b) for b in node.id)
            print(f"  Node {i}: ID {nid}, {len(node.muscles)} muscles")
        
        # Start sampling
        sample_current(node_list, args.duration, args.interval, args.outfile)
        
    except ImportError as e:
        print(f"Hardware not found: {e}")
        print("This means no Thermoflex devices were detected on USB ports.")
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("Shutting down...")
        success = tf.endAll(timeout=5.0)
        if success:
            print("Clean shutdown completed")
        else:
            print("Warning: Shutdown may not have completed cleanly")


if __name__ == '__main__':
    main() 
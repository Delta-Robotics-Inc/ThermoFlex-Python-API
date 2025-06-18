"""
Current Reading Diagnostic Tool

This script helps diagnose issues with current readings from Thermoflex nodes.
It provides detailed information about the status data structure and timing.
"""

import time
import thermoflex as tf


def diagnose_current_readings():
    """
    Comprehensive diagnostic for current reading issues
    """
    print("=== THERMOFLEX CURRENT READING DIAGNOSTIC ===\n")
    
    try:
        # Step 1: Discovery
        print("1. Discovering networks...")
        nets = tf.discover([105])
        print(f"   Found {len(nets)} networks")
        
        # Step 2: Device refresh
        print("2. Refreshing devices...")
        for net in nets:
            net.refreshDevices()
        
        # Step 3: Wait for discovery
        print("3. Waiting for device discovery...")
        time.sleep(3.0)  # Give more time for discovery
        
        # Step 4: Check nodes
        node_list = [node for net in nets for node in net.node_list]
        print(f"4. Found {len(node_list)} nodes total")
        
        if not node_list:
            print("   ERROR: No nodes discovered!")
            return
        
        # Step 5: Detailed node analysis
        for node_idx, node in enumerate(node_list):
            print(f"\n=== NODE {node_idx} ANALYSIS ===")
            print(f"Node ID: {'.'.join(str(b) for b in node.id)}")
            print(f"Network: {node.net.idnum}")
            print(f"Number of muscles: {len(node.muscles)}")
            
            # Step 6: Initial status check
            print("Requesting initial status...")
            try:
                node.status("compact")
                time.sleep(0.5)  # Wait for response
                print("   Status request sent successfully")
            except Exception as e:
                print(f"   ERROR sending status request: {e}")
                continue
            
            # Step 7: Check each muscle
            for muscle_key, muscle in node.muscles.items():
                print(f"\n--- Muscle {muscle_key} ---")
                print(f"Port number: {muscle.portNum}")
                print(f"MOSFET number: {muscle.mosfetnum}")
                print(f"Control mode: {muscle.cmode}")
                print(f"Enable status: {muscle.enable_status}")
                print(f"Train state: {muscle.train_state}")
                
                # Step 8: Analyze SMA_status structure
                print("SMA_status analysis:")
                sma_status = muscle.SMA_status
                
                if not sma_status:
                    print("   WARNING: SMA_status is empty or None!")
                    continue
                
                for key, value in sma_status.items():
                    if key in ['load_amps', 'load_voltdrop', 'pwm_out']:  # Focus on key measurements
                        print(f"   {key}:")
                        print(f"     Type: {type(value)}")
                        print(f"     Value: {value}")
                        
                        if isinstance(value, list):
                            print(f"     List length: {len(value)}")
                            if value:
                                print(f"     First element: {value[0]} (type: {type(value[0])})")
                            else:
                                print("     List is empty - this is likely the problem!")
                
                # Step 9: Test multiple status requests
                print("\nTesting timing with multiple status requests...")
                for i in range(3):
                    print(f"   Request {i+1}:")
                    try:
                        node.status("compact")
                        time.sleep(0.3)  # Wait for response
                        
                        load_amps = muscle.SMA_status.get('load_amps', [])
                        if isinstance(load_amps, list) and load_amps:
                            current = load_amps[0]
                            print(f"     SUCCESS: Current = {current:.6f} A")
                        elif load_amps and not isinstance(load_amps, list):
                            print(f"     SUCCESS: Current = {load_amps:.6f} A (direct value)")
                        else:
                            print(f"     FAILED: No current data (load_amps = {load_amps})")
                    
                    except Exception as e:
                        print(f"     ERROR: {e}")
                
                # Step 10: Test with dump status
                print("\nTesting with 'dump' status...")
                try:
                    node.status("dump")
                    time.sleep(0.5)  # Wait longer for dump response
                    
                    load_amps = muscle.SMA_status.get('load_amps', [])
                    if isinstance(load_amps, list) and load_amps:
                        current = load_amps[0]
                        print(f"   DUMP SUCCESS: Current = {current:.6f} A")
                    else:
                        print(f"   DUMP FAILED: load_amps = {load_amps}")
                        
                except Exception as e:
                    print(f"   DUMP ERROR: {e}")
        
        # Step 11: Network thread analysis
        print(f"\n=== NETWORK THREAD ANALYSIS ===")
        for net in nets:
            print(f"Network {net.idnum}:")
            print(f"   Serial thread alive: {net._serial_thread.is_alive() if net._serial_thread else 'None'}")
            print(f"   Command buffer length: {len(net.command_buff)}")
            print(f"   Received command buffer length: {len(net.rec_cmd_buff)}")
    
    except Exception as e:
        print(f"DIAGNOSTIC ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n=== SHUTTING DOWN ===")
        tf.endAll(timeout=5.0)


def simple_current_test():
    """
    Simple test to just get one current reading
    """
    print("=== SIMPLE CURRENT TEST ===\n")
    
    try:
        # Get first node
        node = tf.get_usb_node(timeout=10.0)
        print(f"Connected to node: {'.'.join(str(b) for b in node.id)}")
        
        # Get first muscle
        muscle = node.muscle0
        print(f"Testing muscle 0 (port {muscle.portNum})")
        
        # Request status and wait
        print("Requesting status...")
        node.status("compact")
        time.sleep(1.0)
        
        # Check data
        load_amps = muscle.SMA_status.get('load_amps', [])
        print(f"Raw load_amps data: {load_amps} (type: {type(load_amps)})")
        
        if isinstance(load_amps, list) and load_amps:
            current = load_amps[0]
            print(f"SUCCESS: Current reading = {current:.6f} A")
        else:
            print("FAILED: No current data available")
            print("This suggests either:")
            print("1. Node is not responding to status requests")
            print("2. Muscle is not connected/enabled")
            print("3. Timing issue with status updates")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        tf.endAll()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Diagnose current reading issues')
    parser.add_argument('--simple', action='store_true', help='Run simple test instead of full diagnostic')
    args = parser.parse_args()
    
    if args.simple:
        simple_current_test()
    else:
        diagnose_current_readings() 
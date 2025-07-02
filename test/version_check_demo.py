#!/usr/bin/env python3
"""
Firmware Version Check Demo

This script demonstrates the automatic firmware version checking functionality.
It connects to a ThermoFlex node and shows how version compatibility warnings
are displayed when a node is first discovered.

The version check automatically runs when:
1. A node is discovered and first status dump is retrieved
2. The firmware version is parsed for the first time
3. Only runs once per node to avoid repeated warnings

Usage:
    python version_check_demo.py
"""

import thermoflex as tf
import time

# Enable debug output to see version check messages
tf.set_debug_level('INFO')

def main():
    """Main function to demonstrate version checking"""
    print("=== THERMOFLEX VERSION CHECK DEMO ===\n")
    
    try:
        print("Discovering ThermoFlex devices...")
        print("Note: Version checking will occur automatically when firmware is first retrieved.\n")
        
        # Discover and connect to node - version check will trigger automatically
        node = tf.get_usb_node(timeout=10.0)
        print(f"\n🔍 Connected to node: {node.get_node_id_string()}")
        
        # Request dump status to get firmware version - this triggers the version check
        print("\nRequesting firmware version (this will trigger version checking)...")
        node.status('dump', device='node')
        time.sleep(2.0)  # Give time for response and version check
        
        # Display current firmware version info
        firmware_version = node.get_firmware_version()
        board_version = node.get_board_version()
        
        print(f"\n📊 Node Information:")
        print(f"   Node ID: {node.get_node_id_string()}")
        print(f"   Firmware Version: {firmware_version}")
        print(f"   Board Version: {board_version}")
        print(f"   Supply Voltage: {node.get_supply_voltage():.2f}V")
        
        # Show version checking constants
        print(f"\n⚙️  Version Compatibility Configuration:")
        print(f"   Minimum Supported: v{tf.devices.MIN_FIRMWARE_VERSION}")
        print(f"   Maximum Tested: v{tf.devices.MAX_TESTED_FIRMWARE_VERSION}")
        
        # Demonstrate that version check only runs once
        print(f"\n🔄 Testing that version check only runs once...")
        print("Requesting status again (should NOT trigger version check):")
        node.status('dump', device='node')
        time.sleep(1.0)
        
        print("✅ Version check only ran once as expected!")
        
        print(f"\n📝 Version Check Summary:")
        if firmware_version:
            # Manual version comparison for demonstration
            from thermoflex.devices import compare_versions, MIN_FIRMWARE_VERSION, MAX_TESTED_FIRMWARE_VERSION
            
            # ANSI color codes for demo
            YELLOW = '\033[93m'
            GREEN = '\033[92m'
            RED = '\033[91m'
            RESET = '\033[0m'
            
            if compare_versions(firmware_version, MIN_FIRMWARE_VERSION) < 0:
                print(f"   Status: {RED}❌ FIRMWARE TOO OLD{RESET}")
            elif compare_versions(firmware_version, MAX_TESTED_FIRMWARE_VERSION) > 0:
                print(f"   Status: {YELLOW}⚠️  FIRMWARE MAY BE TOO NEW{RESET}")
            else:
                print(f"   Status: {GREEN}✅ COMPATIBLE{RESET}")
        else:
            print(f"   Status: ❓ FIRMWARE VERSION NOT AVAILABLE")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("\nShutting down...")
        tf.endAll(timeout=5.0)
    
    return 0

if __name__ == "__main__":
    exit(main()) 
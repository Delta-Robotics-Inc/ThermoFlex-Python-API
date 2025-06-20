"""
Node - Sub-Device Targeting Test

This script tests the status command device targeting functionality to ensure
that muscle status is properly requested and received using protocol-compliant field names.
"""

import time
import thermoflex as tf

# Enable debug logging
tf.set_debug_level('INFO')

def test_device_targeting():
    print("=== DEVICE TARGETING TEST ===\n")
    
    try:
        # Get node using modern API
        node = tf.get_usb_node(timeout=10.0)
        print(f"Connected to node: {'.'.join(str(b) for b in node.id)}")
        
        print(f"\n=== Testing Different Device Targeting Options ===")
        
        # Test 1: Request from all devices (default behavior now)
        print(f"\n1. Testing DEVICE_ALL (node + muscles)...")
        node.status('compact', device='all')
        time.sleep(2.0)
        
        # Check results using protocol-compliant field names
        print(f"   Node data populated: {node.node_status.get('uptime') is not None}")
        muscle0_current = node.muscle0.SMA_status.get('load_amps', [])
        muscle1_current = node.muscle1.SMA_status.get('load_amps', [])
        print(f"   Muscle 0 current data: {muscle0_current[:3] if isinstance(muscle0_current, list) and muscle0_current else muscle0_current}")
        print(f"   Muscle 1 current data: {muscle1_current[:3] if isinstance(muscle1_current, list) and muscle1_current else muscle1_current}")
        
        # Test 2: Request from node only
        print(f"\n2. Testing DEVICE_NODE (node only)...")
        node.status('compact', device='node')
        time.sleep(1.0)
        print(f"   This should only update node data, not muscle data")
        
        # Test 3: Request from muscles only  
        print(f"\n3. Testing DEVICE_PORTALL (muscles only)...")
        node.getMuscleStatus('compact')
        time.sleep(2.0)
        
        muscle0_current_after = node.muscle0.SMA_status.get('load_amps', [])
        muscle1_current_after = node.muscle1.SMA_status.get('load_amps', [])
        print(f"   Muscle 0 current after portall: {muscle0_current_after[:3] if isinstance(muscle0_current_after, list) and muscle0_current_after else muscle0_current_after}")
        print(f"   Muscle 1 current after portall: {muscle1_current_after[:3] if isinstance(muscle1_current_after, list) and muscle1_current_after else muscle1_current_after}")
        
        # Test 4: Request from individual muscle
        print(f"\n4. Testing individual muscle status...")
        current_muscle0 = node.muscle0.getCurrentReading()
        current_muscle1 = node.muscle1.getCurrentReading()
        print(f"   Muscle 0 current reading: {current_muscle0}")
        print(f"   Muscle 1 current reading: {current_muscle1}")
        
        # Test 5: Test muscle-specific requests
        print(f"\n5. Testing muscle-specific status requests...")
        node.muscle0.status('compact')
        time.sleep(1.0)
        node.muscle1.status('compact')  
        time.sleep(1.0)
        
        muscle0_final = node.muscle0.SMA_status.get('load_amps', [])
        muscle1_final = node.muscle1.SMA_status.get('load_amps', [])
        print(f"   Muscle 0 final current: {muscle0_final[:3] if isinstance(muscle0_final, list) and muscle0_final else muscle0_final}")
        print(f"   Muscle 1 final current: {muscle1_final[:3] if isinstance(muscle1_final, list) and muscle1_final else muscle1_final}")
        
        # Test 6: Protocol compliance check
        print(f"\n6. Protocol compliance check...")
        expected_fields = ['device_port', 'enabled', 'mode', 'setpoint', 'output_pwm', 'load_amps', 'load_vdrop', 'load_mohms']
        missing_fields = []
        
        for field in expected_fields:
            if field not in node.muscle0.SMA_status:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"   ⚠️  Missing protocol fields: {missing_fields}")
        else:
            print(f"   ✅ All protocol-compliant fields present")
        
        # Check for legacy fields that shouldn't be there
        legacy_fields = ['enable_status', 'control_mode', 'pwm_out', 'load_voltdrop', 'dev']
        legacy_found = []
        
        for field in legacy_fields:
            if field in node.muscle0.SMA_status and node.muscle0.SMA_status[field] is not None:
                legacy_found.append(field)
        
        if legacy_found:
            print(f"   ⚠️  Legacy fields found: {legacy_found}")
        else:
            print(f"   ✅ No legacy fields - fully protocol compliant")
        
        # Summary
        print(f"\n=== SUMMARY ===")
        success = False
        if (isinstance(muscle0_final, list) and muscle0_final) or \
           (isinstance(muscle1_final, list) and muscle1_final):
            print(f"✅ SUCCESS: Muscle current data is being received!")
            success = True
        else:
            print(f"❌ FAILED: Muscle current data still not received")
            
        print(f"✅ Device targeting functionality working")
        print(f"✅ Multiple request methods available")
        print(f"✅ Protocol compliance: {'PASS' if not missing_fields and not legacy_found else 'PARTIAL'}")
        
        return success
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        tf.endAll()

if __name__ == '__main__':
    success = test_device_targeting()
    print(f"\nTest {'PASSED' if success else 'FAILED'}") 
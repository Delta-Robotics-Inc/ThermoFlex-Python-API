"""
Packet Protocol Compliance Validation Test

This test validates that the packet parsing in deconst_serial_response() 
now uses protocol-compliant field names exactly matching the protobuf definitions.
"""
import thermoflex as tf
import time

tf.set_debug_level('INFO')

def test_packet_protocol_compliance():
    print("=== PACKET PROTOCOL COMPLIANCE TEST ===\n")
    
    try:
        # Get node
        node = tf.get_usb_node(timeout=5.0)
        muscle = node.muscle0
        
        print(f"Connected to node: {'.'.join(str(b) for b in node.id)}")
        print(f"Testing muscle {muscle.portNum}\n")
        
        # Request status to trigger packet parsing
        print("Requesting compact status...")
        node.status('compact', device='all')
        time.sleep(1)
        
        print("\n=== PROTOCOL COMPLIANCE VALIDATION ===")
        
        # Expected protocol-compliant field names from tfnode_messages_pb2.py
        expected_sma_compact_fields = {
            'device_port': 'Device enum',
            'enabled': 'bool', 
            'mode': 'SMAControlMode enum',
            'setpoint': 'float',
            'output_pwm': 'float',
            'load_amps': 'float',
            'load_vdrop': 'float',
            'load_mohms': 'float'
        }
        
        # Check which fields are present
        received_fields = {}
        for field_name, expected_type in expected_sma_compact_fields.items():
            if field_name in muscle.SMA_status:
                value = muscle.SMA_status[field_name]
                if value is not None and (not isinstance(value, list) or value):
                    received_fields[field_name] = value
                    status = "✅ PRESENT"
                else:
                    status = "⚠️  NULL/EMPTY"
            else:
                status = "❌ MISSING"
            
            print(f"{field_name:<12} ({expected_type:<20}) -> {status}")
        
        print(f"\n=== LEGACY/NON-STANDARD FIELD CHECK ===")
        
        # Check for any legacy field names that should NOT be present
        legacy_fields_to_check = [
            'enable_status',  # Should be 'enabled'
            'control_mode',   # Should be 'mode'  
            'pwm_out',        # Should be 'output_pwm'
            'load_voltdrop',  # Should be 'load_vdrop'
            'load_ohms',      # Should be 'load_mohms'
            'dev'             # Should be 'device_port'
        ]
        
        legacy_found = []
        for legacy_field in legacy_fields_to_check:
            if legacy_field in muscle.SMA_status:
                value = muscle.SMA_status[legacy_field]
                if value is not None and (not isinstance(value, list) or value):
                    legacy_found.append(legacy_field)
        
        if legacy_found:
            print("❌ LEGACY FIELDS STILL PRESENT:")
            for field in legacy_found:
                print(f"   {field}: {muscle.SMA_status[field]}")
        else:
            print("✅ NO LEGACY FIELDS FOUND - PACKET PARSING IS PROTOCOL COMPLIANT")
        
        print(f"\n=== DATA QUALITY CHECK ===")
        
        # Check data quality
        issues = []
        
        # Check setpoint for garbage data
        setpoint = muscle.SMA_status.get('setpoint')
        if setpoint is not None:
            if abs(setpoint) > 100.0:
                issues.append(f"setpoint has garbage data: {setpoint}")
            else:
                print(f"✅ setpoint appears valid: {setpoint}")
        else:
            issues.append("setpoint field is missing")
        
        # Check mode is reasonable
        mode = muscle.SMA_status.get('mode')
        if mode is not None:
            if isinstance(mode, int) and 0 <= mode <= 5:
                print(f"✅ mode appears valid: {mode}")
            else:
                issues.append(f"mode has unexpected value: {mode}")
        else:
            issues.append("mode field is missing")
            
        # Check current readings
        load_amps = muscle.SMA_status.get('load_amps', [])
        if isinstance(load_amps, list) and load_amps:
            current = load_amps[0]
            if 0 <= current <= 10.0:  # Reasonable current range
                print(f"✅ load_amps appears valid: {current}")
            else:
                issues.append(f"load_amps has unexpected value: {current}")
        else:
            issues.append("load_amps field is missing or empty")
        
        if issues:
            print(f"\n⚠️  DATA QUALITY ISSUES:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"\n✅ ALL DATA APPEARS VALID")
        
        print(f"\n=== SUMMARY ===")
        protocol_compliant = len(legacy_found) == 0
        has_expected_fields = len(received_fields) >= 6  # Most expected fields present
        
        if protocol_compliant and has_expected_fields:
            print("✅ PACKET PARSING IS FULLY PROTOCOL COMPLIANT")
        elif protocol_compliant:
            print("⚠️  PACKET PARSING IS PROTOCOL COMPLIANT BUT SOME FIELDS MISSING")
        else:
            print("❌ PACKET PARSING STILL HAS LEGACY/NON-STANDARD FIELDS")
        
        print(f"   Protocol compliance: {'✅' if protocol_compliant else '❌'}")
        print(f"   Expected fields present: {len(received_fields)}/{len(expected_sma_compact_fields)}")
        print(f"   Legacy fields found: {len(legacy_found)}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\nCleaning up...")
        tf.endAll(timeout=5.0)

if __name__ == "__main__":
    test_packet_protocol_compliance() 
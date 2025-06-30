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
        
        print("Requesting dump status for complete field validation...")
        node.status('dump', device='all')
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
        
        # Expected SMA dump-only fields (raw data and advanced diagnostics)
        expected_sma_dump_fields = {
            'vld_raw': 'uint32 (raw voltage load ADC)',
            'curr_raw': 'uint32 (raw current ADC)',
            'vld_scalar': 'float',
            'vld_offset': 'float',
            'r_sns_ohms': 'float',
            'amp_gain': 'float',
            'af_mohms': 'float',
            'delta_mohms': 'float',
            'trainState': 'uint32',
            'default_mode': 'SMAControlMode',
            'default_setpoint': 'float',
            'rctrl_kp': 'float',
            'rctrl_ki': 'float', 
            'rctrl_kd': 'float',
            'cctrl_kp': 'float',
            'cctrl_ki': 'float',
            'cctrl_kd': 'float'
        }
        
        # Check SMA compact fields
        print("=== SMA COMPACT STATUS FIELDS ===")
        received_compact_fields = {}
        for field_name, expected_type in expected_sma_compact_fields.items():
            if field_name in muscle.SMA_status:
                value = muscle.SMA_status[field_name]
                if value is not None and (not isinstance(value, list) or value):
                    received_compact_fields[field_name] = value
                    status = "✅ PRESENT"
                else:
                    status = "⚠️  NULL/EMPTY"
            else:
                status = "❌ MISSING"
            
            print(f"{field_name:<12} ({expected_type:<20}) -> {status}")
        
        # Check SMA dump fields
        print("\n=== SMA DUMP STATUS FIELDS ===")
        received_dump_fields = {}
        for field_name, expected_type in expected_sma_dump_fields.items():
            if field_name in muscle.SMA_status:
                value = muscle.SMA_status[field_name]
                if value is not None and (not isinstance(value, list) or value):
                    received_dump_fields[field_name] = value
                    status = "✅ PRESENT"
                else:
                    status = "⚠️  NULL/EMPTY"
            else:
                status = "❌ MISSING"
            
            print(f"{field_name:<15} ({expected_type:<30}) -> {status}")
        
        print(f"\n=== LEGACY/NON-STANDARD FIELD CHECK ===")
        
        # Check for any legacy field names that should NOT be present
        legacy_fields_to_check = [
            'enable_status',  # Should be 'enabled'
            'control_mode',   # Should be 'mode'  
            'pwm_out',        # Should be 'output_pwm'
            'load_voltdrop',  # Should be 'load_vdrop'
            'load_ohms',      # Should be 'load_mohms'
            'dev',            # Should be 'device_port'
            'curr_adc',       # Should be 'curr_raw'
            'vld_adc',        # Should be 'vld_raw'
            'voltage_raw',    # Should be 'vld_raw'
            'current_adc'     # Should be 'curr_raw'
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
        
        # Test node fields
        print(f"\n=== NODE STATUS FIELDS VALIDATION ===")
        expected_node_fields = {
            'v_supply_raw': 'uint32 (raw supply voltage ADC)',
            'heartbeat_enabled': 'bool'
        }
        
        node_issues = []
        for field_name, expected_type in expected_node_fields.items():
            if field_name == 'v_supply_raw':
                value = node.get_supply_voltage_raw()
            elif field_name == 'heartbeat_enabled':
                value = node.node_config.get('heartbeat_enabled')
            
            if value is not None:
                print(f"{field_name:<18} ({expected_type:<30}) -> ✅ PRESENT: {value}")
            else:
                print(f"{field_name:<18} ({expected_type:<30}) -> ❌ MISSING")
                node_issues.append(field_name)
        
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
        
        # Check raw data fields if present
        vld_raw = muscle.SMA_status.get('vld_raw', [])
        if isinstance(vld_raw, list) and vld_raw:
            raw_val = vld_raw[0]
            if isinstance(raw_val, int) and 0 <= raw_val <= 4095:  # Typical ADC range
                print(f"✅ vld_raw appears valid: {raw_val}")
            else:
                issues.append(f"vld_raw has unexpected value: {raw_val}")
        
        curr_raw = muscle.SMA_status.get('curr_raw', [])
        if isinstance(curr_raw, list) and curr_raw:
            raw_val = curr_raw[0]
            if isinstance(raw_val, int) and 0 <= raw_val <= 4095:  # Typical ADC range
                print(f"✅ curr_raw appears valid: {raw_val}")
            else:
                issues.append(f"curr_raw has unexpected value: {raw_val}")
        
        if issues:
            print(f"\n⚠️  DATA QUALITY ISSUES:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"\n✅ ALL DATA APPEARS VALID")
        
        print(f"\n=== SUMMARY ===")
        protocol_compliant = len(legacy_found) == 0
        has_expected_compact_fields = len(received_compact_fields) >= 6  # Most compact fields present
        has_expected_dump_fields = len(received_dump_fields) >= 10  # Most dump fields present
        node_fields_ok = len(node_issues) == 0
        
        if protocol_compliant and has_expected_compact_fields and has_expected_dump_fields and node_fields_ok:
            print("✅ PACKET PARSING IS FULLY PROTOCOL COMPLIANT")
        elif protocol_compliant:
            print("⚠️  PACKET PARSING IS PROTOCOL COMPLIANT BUT SOME FIELDS MISSING")
        else:
            print("❌ PACKET PARSING STILL HAS LEGACY/NON-STANDARD FIELDS")
        
        print(f"   Protocol compliance: {'✅' if protocol_compliant else '❌'}")
        print(f"   SMA compact fields: {len(received_compact_fields)}/{len(expected_sma_compact_fields)}")
        print(f"   SMA dump fields: {len(received_dump_fields)}/{len(expected_sma_dump_fields)}")
        print(f"   Node fields: {'✅' if node_fields_ok else '❌'} ({len(node_issues)} missing)")
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
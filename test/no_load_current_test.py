#!/usr/bin/env python3
"""
No-Load Current Measurement Test

This script demonstrates the proper way to measure no-load current from ThermoFlex muscles.
For accurate no-load current measurement, the muscle must be:
1. Set to PWM (percent) mode
2. Set to 0% setpoint 
3. ENABLED (not disabled)

This is different from just getting current while disabled, which may not give accurate readings.
"""

import thermoflex as tf
import time

# Enable debug output
tf.set_debug_level('INFO')

def setup_muscle_for_no_load_measurement(muscle, measurement_time=2.0):
    """Set up muscle for proper no-load current measurement and return the reading.
    
    Args:
        muscle: Muscle object to configure
        measurement_time: Time to wait for stabilization
        
    Returns:
        float: No-load current in amps, or None if failed
    """
    try:
        print(f"   Setting up muscle for no-load measurement...")
        
        # 1. Set to PWM (percent) mode
        muscle.setMode("percent")
        print(f"     ✓ Set to PWM mode")
        
        # 2. Set setpoint to 0% (no PWM output)
        muscle.setSetpoint(conmode="percent", setpoint=0.0)
        print(f"     ✓ Set setpoint to 0%")
        
        # 3. Enable the muscle (critical for accurate current measurement)
        muscle.setEnable(True)
        print(f"     ✓ Enabled muscle (required for accurate current measurement)")
        
        # Wait for stabilization
        print(f"     ⏳ Waiting {measurement_time}s for stabilization...")
        time.sleep(measurement_time)
        
        # Get fresh status
        muscle.status('compact')
        time.sleep(0.1)
        
        # Get the current reading
        no_load_current = muscle.get_current()
        print(f"     📊 No-load current measured: {no_load_current} A")
        
        return no_load_current
        
    except Exception as e:
        print(f"     ❌ Error during no-load measurement: {e}")
        return None

def test_no_load_current():
    """Test and compare different current measurement methods"""
    print("=== NO-LOAD CURRENT MEASUREMENT TEST ===\n")
    
    try:
        # Get node
        node = tf.get_usb_node(timeout=10.0)
        print(f"Connected to node: {node.get_node_id_string()}")
        
        # Get muscle to test
        muscle = node.muscle0
        print(f"Testing muscle on port {muscle.get_port_number()}")
        
        print(f"\n=== Method Comparison ===")
        
        # Method 1: Current while disabled (incorrect for no-load measurement)
        print(f"\n1. Testing current while muscle is DISABLED (incorrect method):")
        muscle.setEnable(False)
        time.sleep(1.0)
        muscle.status('compact')
        time.sleep(0.5)
        disabled_current = muscle.get_current()
        print(f"   Current while disabled: {disabled_current} A")
        print(f"   ⚠️  This may not be accurate no-load current!")
        
        # Method 2: Proper no-load current measurement
        print(f"\n2. Testing proper no-load current measurement:")
        print(f"   Setting muscle to PWM mode, 0% setpoint, ENABLED...")
        no_load_current = setup_muscle_for_no_load_measurement(muscle, measurement_time=3.0)
        print(f"   ✅ No-load current (proper method): {no_load_current} A")
        
        # Method 3: Manual setup (same as method 2 but step-by-step)
        print(f"\n3. Manual no-load setup (verification):")
        muscle.setMode("percent")  # PWM mode
        muscle.setSetpoint(conmode="percent", setpoint=0.0)  # 0% setpoint
        muscle.setEnable(True)  # ENABLED (critical!)
        time.sleep(2.0)  # Wait for stabilization
        muscle.status('compact')
        time.sleep(0.5)
        manual_no_load = muscle.get_current()
        print(f"   Manual no-load current: {manual_no_load} A")
        
        # Analysis
        print(f"\n=== Analysis ===")
        if disabled_current is not None and no_load_current is not None:
            if abs(disabled_current - no_load_current) > 0.01:  # 10mA difference
                print(f"   📊 Significant difference detected!")
                print(f"   📊 Disabled current: {disabled_current:.4f} A")
                print(f"   📊 No-load current:  {no_load_current:.4f} A")
                print(f"   📊 Difference: {abs(disabled_current - no_load_current):.4f} A")
                print(f"   ✅ Use the no-load current measurement for accurate readings")
            else:
                print(f"   📊 Measurements are similar (difference < 10mA)")
                print(f"   📊 Both methods give: ~{no_load_current:.4f} A")
        
        if manual_no_load is not None and no_load_current is not None:
            print(f"   ✅ Manual vs automatic methods match: {abs(manual_no_load - no_load_current) < 0.001}")
        
        # Clean up
        print(f"\n=== Cleanup ===")
        muscle.setEnable(False)
        print("   Muscle disabled for safety")
        
        # Show additional muscle info
        print(f"\n=== Additional Muscle Information ===")
        print(f"   Muscle ID: {muscle.get_muscle_id()}")
        print(f"   Enabled: {muscle.is_enabled()}")
        print(f"   Mode: {muscle.get_mode()}")
        print(f"   Setpoint: {muscle.get_setpoint()}")
        print(f"   Resistance: {muscle.get_resistance()} mΩ")
        print(f"   Voltage Drop: {muscle.get_voltage_drop()} V")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\nShutting down...")
        tf.endAll(timeout=5.0)

def main():
    """Main function"""
    print(__doc__)
    success = test_no_load_current()
    
    if success:
        print("\n✅ No-load current test completed successfully!")
        print("\n💡 Key Takeaway:")
        print("   For accurate no-load current: PWM mode, 0% setpoint, ENABLED")
        print("   Manual setup: muscle.setMode('percent'), setSetpoint(0.0), setEnable(True)")
    else:
        print("\n❌ Test failed!")
    
    return 0 if success else 1

if __name__ == '__main__':
    exit(main()) 
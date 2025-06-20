#!/usr/bin/env python3
"""
Device Status Dump Script

This script displays all available status information from ThermoFlex nodes and muscles
using the clean accessor methods. Provides a comprehensive view of device state.

Usage:
    python device-status-dump.py
"""

import thermoflex as tf
import time

# Enable debug output
tf.set_debug_level('INFO')

def dump_node_status(node):
    """Display all node status information using accessor methods"""
    print("=" * 60)
    print(f"NODE STATUS: {node.get_node_id_string()}")
    print("=" * 60)
    
    # Basic node information
    print(f"Node ID:                {node.get_node_id_string()}")
    print(f"Firmware Version:       {node.get_firmware_version()}")
    print(f"Board Version:          {node.get_board_version()}")
    print(f"CAN ID:                 {node.get_can_id()}")
    print(f"Active Status:          {node.get_node_active_status()}")
    
    # Power and timing
    print(f"Supply Voltage:         {node.get_supply_voltage()} V")
    print(f"Uptime:                 {node.get_uptime()} ms")
    
    # Error status
    print(f"Has Errors:             {node.has_errors()}")
    print(f"Current Error Code:     {node.get_error_code()}")
    error_history = node.get_error_history()
    if error_history:
        print(f"Error History:          {error_history[:5]}")  # Show last 5 errors
    
    # Sensor readings
    print(f"Potentiometer Value:    {node.get_potentiometer_value()}")
    
    # Configuration (dump status only)
    print(f"Log Interval:           {node.get_log_interval()} ms")
    print(f"Max Current Limit:      {node.get_max_current()} A")
    print(f"Min Supply Voltage:     {node.get_min_supply_voltage()} V")
    print(f"Voltage Divider Scalar: {node.get_voltage_divider_scalar()}")
    print(f"Voltage Divider Offset: {node.get_voltage_divider_offset()}")
    
    print()

def dump_muscle_status(muscle, muscle_name):
    """Display all muscle status information using accessor methods"""
    print("-" * 50)
    print(f"MUSCLE STATUS: {muscle_name}")
    print("-" * 50)
    
    # Basic muscle information
    print(f"Muscle ID:              {muscle.get_muscle_id()}")
    print(f"Port Number:            {muscle.get_port_number()}")
    print(f"Device Port Enum:       {muscle.get_device_port()}")
    
    # Control status
    print(f"Enabled:                {muscle.is_enabled()}")
    print(f"Control Mode:           {muscle.get_mode()}")
    print(f"Setpoint:               {muscle.get_setpoint()}")
    print(f"PWM Output:             {muscle.get_output_pwm()}")
    
    # Real-time measurements
    print(f"Current:                {muscle.get_current()} A")
    print(f"Voltage Drop:           {muscle.get_voltage_drop()} V")
    print(f"Resistance:             {muscle.get_resistance()} mΩ")
    
    # Historical data (show last few readings)
    current_history = muscle.get_current_history()
    resistance_history = muscle.get_resistance_history()
    if current_history:
        print(f"Current History (last 3): {current_history[:3]} A")
    if resistance_history:
        print(f"Resistance History (last 3): {resistance_history[:3]} mΩ")
    
    # Training state
    print(f"Train State:            {muscle.get_train_state()}")
    
    # Default/Configuration values (dump status only)
    print(f"Default Mode:           {muscle.get_default_mode()}")
    print(f"Default Setpoint:       {muscle.get_default_setpoint()}")
    
    # PID Controller settings (dump status only)
    print(f"PID Kp (Proportional): {muscle.get_pid_kp()}")
    print(f"PID Ki (Integral):      {muscle.get_pid_ki()}")
    print(f"PID Kd (Derivative):    {muscle.get_pid_kd()}")
    
    # Advanced diagnostic values (dump status only)
    print(f"Voltage Load Scalar:    {muscle.get_voltage_load_scalar()}")
    print(f"Voltage Load Offset:    {muscle.get_voltage_load_offset()}")
    print(f"Sense Resistance:       {muscle.get_sense_resistance()} Ω")
    print(f"Amplifier Gain:         {muscle.get_amplifier_gain()}")
    
    print()

def main():
    """Main function to dump all device status"""
    print("=== THERMOFLEX DEVICE STATUS DUMP ===\n")
    
    try:
        # Discover and connect to node
        print("Discovering ThermoFlex devices...")
        node = tf.get_usb_node(timeout=10.0)
        print(f"✅ Connected to node: {node.get_node_id_string()}\n")
        
        # Request comprehensive status from all devices
        print("Requesting compact status...")
        node.status('compact', device='all')
        time.sleep(1.0)
        
        print("Requesting dump status for complete information...")
        node.status('dump', device='all')
        time.sleep(2.0)  # Give more time for dump status
        
        print("Processing status data...\n")
        
        # Dump node status
        dump_node_status(node)
        
        # Dump status for all muscles
        for muscle_key, muscle in node.muscles.items():
            muscle_name = f"Muscle {muscle_key} (Port {muscle.get_port_number()})"
            dump_muscle_status(muscle, muscle_name)
        
        print("=" * 60)
        print("STATUS DUMP COMPLETE")
        print("=" * 60)
        print(f"Total muscles found: {len(node.muscles)}")
        print(f"Node active: {node.get_node_active_status()}")
        print(f"Supply voltage: {node.get_supply_voltage()} V")
        
        # Summary of enabled muscles
        enabled_muscles = []
        for muscle_key, muscle in node.muscles.items():
            if muscle.is_enabled():
                enabled_muscles.append(f"Muscle {muscle_key}")
        
        if enabled_muscles:
            print(f"Enabled muscles: {', '.join(enabled_muscles)}")
        else:
            print("All muscles are disabled")
        
    except Exception as e:
        print(f"❌ Error during status dump: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("\nShutting down...")
        tf.endAll(timeout=5.0)
    
    return 0

if __name__ == '__main__':
    exit(main()) 
#!/usr/bin/env python3
"""
Configuration System Demo Script

This script demonstrates the core configuration infrastructure and API
functionality added to the ThermoFlex system. It shows:

1. Node-level configuration
2. Muscle-level configuration  
3. PID parameter tuning
4. Configuration validation
5. Configuration state tracking

Usage:
    python configuration_demo.py
"""

import thermoflex as tf
import time


def configure_node_demo(node):
    """Demonstrate node-level configuration"""
    print("\n=== Node Configuration Demo ===")
    
    # Get current configuration (should be empty initially)
    current_config = node.get_node_config()
    print(f"Initial node config: {current_config}")
    
    # Request dump status to populate configuration from device
    print("Requesting dump status to populate current configuration...")
    node.status("dump", device="node")
    time.sleep(0.5)  # Wait for response
    
    # Get configuration after status request
    populated_config = node.get_node_config()
    print(f"Configuration populated from device: {populated_config}")
    
    # Configure node settings
    node_config = {
        'heartbeat_enabled': True,
        'can_id': 0x123
    }
    
    print(f"Configuring node with: {node_config}")
    node.configure_node(node_config, save_to_flash=False)
    
    # Show updated configuration
    updated_config = node.get_node_config()
    print(f"Updated node config: {updated_config}")
    
    # Verify the configuration was applied
    if 'heartbeat_enabled' in updated_config and updated_config['heartbeat_enabled'] == True:
        print("✓ Heartbeat configuration verified")
    else:
        print("✗ Heartbeat configuration not applied correctly")
        
    if 'can_id' in updated_config and updated_config['can_id'] == 0x123:
        print("✓ CAN ID configuration verified")
    else:
        print("✗ CAN ID configuration not applied correctly")
    
    return True


def configure_muscle_demo(muscle):
    """Demonstrate muscle-level configuration"""
    print("\n=== Muscle Configuration Demo ===")
    
    # Get current configuration (should be empty initially)
    current_config = muscle.get_muscle_config()
    print(f"Initial muscle config: {current_config}")
    
    # Request dump status to populate configuration from device
    print("Requesting dump status to populate current configuration...")
    muscle.status("dump")
    time.sleep(0.5)  # Wait for response
    
    # Get configuration after status request
    populated_config = muscle.get_muscle_config()
    print(f"Configuration populated from device: {populated_config}")
    
    # Configure muscle settings
    muscle_config = {
        'default_mode': 'ohms',
        'default_setpoint': 50.0,
        'rctrl_kp': 2.0,
        'rctrl_ki': 0.1,
        'rctrl_kd': 0.05
    }
    
    print(f"Configuring muscle with: {muscle_config}")
    muscle.configure_muscle(muscle_config, save_to_flash=False)
    
    # Show updated configuration
    updated_config = muscle.get_muscle_config()
    print(f"Updated muscle config: {updated_config}")
    
    # Verify the configuration was applied
    verification_checks = [
        ('default_mode', 'ohms'),
        ('default_setpoint', 50.0),
        ('rctrl_kp', 2.0),
        ('rctrl_ki', 0.1),
        ('rctrl_kd', 0.05)
    ]
    
    for key, expected_value in verification_checks:
        if key in updated_config and updated_config[key] == expected_value:
            print(f"✓ {key} configuration verified: {expected_value}")
        else:
            print(f"✗ {key} configuration not applied correctly (expected: {expected_value}, got: {updated_config.get(key)})")
    
    return True


def pid_configuration_demo(muscle):
    """Demonstrate PID parameter configuration"""
    print("\n=== PID Configuration Demo ===")
    
    # Test with negative PID values (should be allowed)
    print("Testing negative PID values (should be allowed)...")
    muscle.configure_pid('resistance', kp=-1.5, ki=0.2, kd=-0.1)
    
    # Configure current controller PID  
    print("Configuring current controller PID...")
    muscle.configure_pid('current', kp=0.8, ki=-0.05, kd=0.02)
    
    # Show updated configuration
    config = muscle.get_muscle_config()
    print(f"Updated PID config: {config}")
    
    # Verify negative values were accepted
    verification_checks = [
        ('rctrl_kp', -1.5),
        ('rctrl_ki', 0.2),
        ('rctrl_kd', -0.1),
        ('cctrl_kp', 0.8),
        ('cctrl_ki', -0.05),
        ('cctrl_kd', 0.02)
    ]
    
    for key, expected_value in verification_checks:
        if key in config and config[key] == expected_value:
            print(f"✓ {key} PID parameter verified: {expected_value}")
        else:
            print(f"✗ {key} PID parameter not applied correctly (expected: {expected_value}, got: {config.get(key)})")
    
    return True


def validation_demo():
    """Demonstrate configuration validation"""
    print("\n=== Configuration Validation Demo ===")
    
    # Create a temporary muscle for validation testing
    temp_muscle = tf.Muscle(_port=0)
    
    try:
        # Test valid configuration
        valid_config = {'default_mode': 'ohms', 'rctrl_kp': 1.0}
        temp_muscle._validate_muscle_config(valid_config)
        print("✓ Valid configuration passed validation")
        
        # Test invalid mode
        invalid_config = {'default_mode': 'invalid_mode'}
        temp_muscle._validate_muscle_config(invalid_config)
        print("✗ Should have failed validation")
        
    except ValueError as e:
        print(f"✓ Invalid configuration correctly rejected: {e}")
    
    try:
        # Test invalid type for PID value
        invalid_config = {'rctrl_kp': 'not_a_number'}
        temp_muscle._validate_muscle_config(invalid_config)
        print("✗ Should have failed validation")
        
    except ValueError as e:
        print(f"✓ Invalid PID type correctly rejected: {e}")
    
    try:
        # Test that negative PID values are now allowed
        valid_negative_config = {'rctrl_kp': -1.0}
        temp_muscle._validate_muscle_config(valid_negative_config)
        print("✓ Negative PID values correctly allowed")
    except ValueError as e:
        print(f"✗ Negative PID values incorrectly rejected: {e}")
    
    return True


def configuration_reset_demo(node, muscle):
    """Demonstrate configuration reset functionality"""
    print("\n=== Configuration Reset Demo ===")
    
    # Reset node to defaults
    print("Resetting node configuration to defaults...")
    node.reset_node_config(to_defaults=True)
    
    # Reset muscle to saved settings
    print("Resetting muscle configuration to saved settings...")  
    muscle.reset_muscle_config(to_defaults=False)
    
    print("Reset commands sent successfully")
    
    return True


def main():
    """Main demonstration function"""
    print("ThermoFlex Configuration System Demo")
    print("====================================")
    
    try:
        # Get the first USB-connected node (like muscle-simple.py)
        print("Discovering ThermoFlex node...")
        node = tf.get_usb_node()
        print(f"✓ Connected to node: {node.get_node_id_string()}")
        
        # Create and attach a muscle (like muscle-simple.py)
        muscle = tf.Muscle(_port=0)  # Port 0 = M1
        node.attachMuscle(muscle, 0)
        print("✓ Muscle attached to port 0")
        
        # Run configuration demonstrations
        configure_node_demo(node)
        configure_muscle_demo(muscle)
        pid_configuration_demo(muscle)
        validation_demo()
        configuration_reset_demo(node, muscle)
        
        print("\n=== Demo Complete ===")
        print("Configuration system is ready for use!")
        print("\nKey Features Demonstrated:")
        print("- Node and muscle configuration")
        print("- PID parameter tuning")
        print("- Parameter validation")
        print("- Configuration state tracking")
        print("- Reset functionality")
        
        return True
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        print("Make sure a ThermoFlex node is connected via USB")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup (like muscle-simple.py)
        print("\nCleaning up...")
        tf.endAll()


if __name__ == "__main__":
    # tf.set_debug_level("DEBUG")  # Uncomment for debug output
    success = main()
    exit(0 if success else 1) 
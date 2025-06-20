'''
Test for ThermoFlex Session Logging - Updated for Protocol Compliance
'''

import thermoflex as tf
import time as t

tf.set_debug_level('INFO')

def test_session_logging():
    print("=== THERMOFLEX SESSION LOGGING TEST ===\n")
    
    try:
        # Use modern API to get node
        node = tf.get_usb_node(timeout=10.0)
        print(f"Connected to node: {'.'.join(str(b) for b in node.id)}")
        
        # Access muscles using modern interface
        muscle1 = node.muscle0  # First muscle (port 0)
        muscle2 = node.muscle1  # Second muscle (port 1)
        
        print(f"Muscle 1 (port {muscle1.portNum})")
        print(f"Muscle 2 (port {muscle2.portNum})")
        
        # Enable logging
        node.setLogmode(1)  # Enable logging
        print("Logging enabled")
        
        # Get initial status
        t.sleep(0.1)
        node.status('compact', device='all')
        t.sleep(1.0)
        
        # Display initial status using protocol-compliant fields
        print(f"\n=== Initial Status (Protocol-Compliant Fields) ===")
        print(f"Node uptime: {node.node_status.get('uptime')}")
        print(f"Supply voltage: {node.node_status.get('volt_supply')}")
        
        for i, muscle in enumerate([muscle1, muscle2]):
            print(f"Muscle {i}:")
            print(f"  enabled: {muscle.SMA_status.get('enabled')}")
            print(f"  mode: {muscle.SMA_status.get('mode')}")
            print(f"  setpoint: {muscle.SMA_status.get('setpoint')}")
            print(f"  load_amps: {muscle.SMA_status.get('load_amps', [])[:3] if muscle.SMA_status.get('load_amps') else 'None'}")
        
        # Select muscle to test
        m_to_train = muscle1  # Test with first muscle
        
        print(f"\n=== Muscle Training Test ===")
        print(f"Testing muscle on port {m_to_train.portNum}")
        
        # Muscle setup
        m_to_train.setMode("percent")
        print("Set mode to percent")
        t.sleep(1)
        
        m_to_train.setSetpoint(conmode="percent", setpoint=0.1)  # Start low for safety
        print("Set setpoint to 0.1 (10%)")
        t.sleep(1)
        
        # Training program timing
        wait1 = 5   # Reduced for testing
        wait2 = 2   # Reduced for testing
        
        print(f"\n=== Test Control Script ===")
        print("Enabling muscle...")
        m_to_train.setEnable(True)
        
        print(f"Running for {wait1} seconds...")
        for i in range(wait1):
            t.sleep(1)
            # Get status update
            m_to_train.status('compact')
            t.sleep(0.1)
            
            # Log the resistance and voltage drop during training using new accessor methods
            current = m_to_train.get_current()
            print(f"Current during training: {current:.3f}A")
            
            resistance = m_to_train.get_resistance()
            print(f"Resistance during training: {resistance:.1f} mΩ")
            
            v_drop = m_to_train.get_voltage_drop()
            print(f"Voltage drop during training: {v_drop:.3f}V")
        
        print("Disabling muscle...")
        m_to_train.setEnable(False)
        t.sleep(wait2)
        
        print("Training sequence complete")
        
        # Final status check
        node.status('compact', device='all')
        t.sleep(1)
        
        print(f"\n=== Final Status ===")
        for i, muscle in enumerate([muscle1, muscle2]):
            print(f"Muscle {i}:")
            print(f"  enabled: {muscle.SMA_status.get('enabled')}")
            print(f"  final current: {muscle.get_current():.3f}A")
        
        print("\n✅ Session logging test completed successfully")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nDisabling all muscles and shutting down...")
        try:
            node.disableAll()
            node.setLogmode(0)  # Disable logging
        except:
            pass
        tf.endAll(timeout=5.0)

if __name__ == "__main__":
    test_session_logging()
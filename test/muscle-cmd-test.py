'''
Unit test for all muscle commands and status variables
'''
import thermoflex as tf
import asyncio
import time as t
import sys
from thermoflex.tools.nodeserial import stop_threads_flag

COMMAND_CHANGE_INTERVAL = 5
STATUS_THREAD_INTERVAL = 10
END_TEST_FLAG = False

tf.set_debug_level('DEBUG')

#Establish a connection to the testnet and testnode
testnode = tf.get_usb_node()

#Test the muscle command and status variables
muscle1 = testnode.muscle0

async def muscle_status_monitor(muscle):
    """Asynchronously monitor muscle status"""
    global END_TEST_FLAG
    
    while not END_TEST_FLAG:
        await asyncio.sleep(STATUS_THREAD_INTERVAL)
        
        if END_TEST_FLAG:
            break
            
        status = muscle.SMA_status
        # Get the current setpoint of the muscle
        setpoint = status['SMA_deafult_setpoint']
        print(f"Muscle Setpoint: {setpoint}")

        # Get the current mode of the muscle
        mode = status['SMA_default_mode']
        print(f"Muscle Mode: {mode}")

        # Get the current current of the muscle
        current = status['load_amps']
        print(f"Muscle Current: {current}")

        # Get the current voltage of the muscle
        voltage = status['load_voltdrop']
        print(f"Muscle Voltage: {voltage}")
        
        # Get the muscle status
        status_string = muscle.muscleStatus()
        print(f"Muscle Status: {status_string}")

        # Get the resistance of the muscle
        resistance = muscle.getResistance()
        print(f"Muscle Resistance: {resistance}")

def test_muscle_commands(muscle):
    """Test muscle commands in the main process"""
    print("Starting muscle command tests...")
    
    # Set the mode of the muscle
    muscle.setMode(conmode="amps")
    print(f"Muscle Mode: {muscle.cmode}")
    t.sleep(COMMAND_CHANGE_INTERVAL)

    # Set a setpoint for the muscle
    muscle.setSetpoint(conmode="percent", setpoint=0.75)
    print("Setpoint set to 0.75 in percent mode.")
    t.sleep(COMMAND_CHANGE_INTERVAL)

    # Enable the muscle
    muscle.setEnable(True)
    print("Muscle enabled.")
    t.sleep(COMMAND_CHANGE_INTERVAL)

    # Disable the muscle
    muscle.setEnable(False)
    print("Muscle disabled.")
    t.sleep(COMMAND_CHANGE_INTERVAL)
    
    print("Muscle command tests completed.")

async def main():
    """Main async function that coordinates the test"""
    global END_TEST_FLAG
    
    # Start the status monitoring task
    status_task = asyncio.create_task(muscle_status_monitor(muscle1))
    
    # Run the muscle command tests in the main process
    # We need to run this in a separate thread to not block the async loop
    def run_commands():
        test_muscle_commands(muscle1)
    
    # Run command tests
    await asyncio.get_event_loop().run_in_executor(None, run_commands)
    
    print("Test complete - waiting 15 seconds before cleanup...")
    
    await asyncio.sleep(15)
    
    # Signal the status monitoring to stop
    END_TEST_FLAG = True
    
    # Wait for status task to complete
    try:
        await asyncio.wait_for(status_task, timeout=5.0)
    except asyncio.TimeoutError:
        print("Status monitoring task did not complete in time, cancelling...")
        status_task.cancel()
    
    print("Ending all connections...")
    
    # Use the improved endAll() function with proper timeout handling
    success = tf.endAll(timeout=10.0, force_timeout=2.0, exit_program=False)
    
    if success:
        print("All threads and connections closed successfully")
    else:
        print("Warning: Some threads may not have closed cleanly")
    
    print("Cleanup completed - program should exit cleanly now")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
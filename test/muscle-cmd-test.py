'''
Unit test for all muscle commands and status variables
'''
import thermoflex as tf
import threading as th
import time as t
import sys

COMMAND_CHANGE_INTERVAL = 5
STATUS_THREAD_INTERVAL =  10
END_TEST_FLAG = th.Event()
END_TEST_FLAG.clear()

def threaded(func):
    global threadlist
    threadlist = []

    def wrapper(*args, **kwargs):
        thread = th.Thread(target=func, args=args, kwargs=kwargs)
        threadlist.append(thread)
        thread.start()
        return thread
    
    return wrapper

#Establish a connection to the testnet and testnode
# networklist = tf.discover()
# testnet = networklist[0]
testnode = tf.get_usb_node()

#Test the muscle command and status variables

muscle1 = testnode.muscle0

# Test the Muscle class methods
@threaded
def test_muscle_cmd(muscle):

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

@threaded
def muscle_status_test(muscle):
        
    while not END_TEST_FLAG.is_set():
        t.sleep(STATUS_THREAD_INTERVAL)
        status = muscle.SMA_status
        # Get the current setpoint of the muscle
        setpoint = status['SMA_deafult_setpoint']
        print(f"Muscle Setpoint: {setpoint}")

        # Get the current mode of the muscle
        mode = status['SMA_default_mode']
        print(f"Muscle Mode: {mode}")

        # Get the current current of the muscle
        current =status['load_amps']
        print(f"Muscle Current: {current}")

        # Get the current voltage of the muscle
        voltage = status['load_voltdrop']
        print(f"Muscle Voltage: {voltage}")
        # Get the muscle status
        
        status = muscle.muscleStatus()
        print(f"Muscle Status: {status}")

        # Get the resistance of the muscle
        resistance = muscle.getResistance()
        print(f"Muscle Resistance: {resistance}")
        


# Run the test
muscle_status_test(muscle1)
test_muscle_cmd(muscle1)
    
t.sleep(60)
END_TEST_FLAG.set()
t.sleep(5)
tf.endAll()

for thread  in threadlist:
    thread.join()


sys.exit(0)
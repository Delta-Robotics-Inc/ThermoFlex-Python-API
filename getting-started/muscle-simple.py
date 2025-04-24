'''
This is a simple example of how to use the ThermoFlex library to control a muscle.
The ThermoFlex library and install instructions can be found here:
https://github.com/Delta-Robotics-Inc/TF-Python-Serial

To run this example, you will need to have a ThermoFlex network set up with at least
one node connected to a muscle.

In other words, connect a ThermoFlex Node Controller to your computer via USB, and
connect a muscle to the Node Controller. For more a complicated newtwork setup using
multiple nodes connected over CAN, see the other examples in this folder.

**NOTE: Be ready to hit the left button on the controller to stop the muscle from moving**
- In the future, a safety feature will be added to prevent the muscle from overheating.
- This safety feature will utilize the resistance of the muscle to determine if it is overheating.
- For now, be ready to stop the muscle from moving if it gets too hot.
'''
import thermoflex as tf
import time

# tf.set_debug_level("DEBUG") # Use for debug if needed

node = tf.get_usb_node() # Discover the first connected node over USB

muscle = tf.Muscle(_port = 0)  # Match portNum to the muscle port number 0=M1, 1=M2
node.attachMuscle(muscle, 0)  # Assign the muscle to the Node at port 0

# Move the Muscle
# NOTE: THESE VALUES ARE FOR THE MK.1 MUSCLE WITH A 12 V SUPPLY
# IF USING A HIGHER SUPPLY, START WITH A SMALL TIME AND INCREASE SLOWLY
# BE READY TO CUT OFF THE POWER IF THE MUSCLE GETS TOO HOT
print("Activating muscle... ")
muscle.setMode("percent")
muscle.setSetpoint("percent", 0.5) # Start at 50%
muscle.setEnable(True)
time.sleep(2)
muscle.setSetpoint("percent", 0.4) # Ramp down to 40%
time.sleep(2)
muscle.setSetpoint("percent", 0.3) # Ramp down to 30%
time.sleep(2)
muscle.setSetpoint("percent", 0.1) # Ramp down to 10%

time.sleep(4)  # Increase if needed but be careful!  There is no safegaurd to prevent the muscle from overheating

print("Deactivating muscle... ")
node.disableAll()

time.sleep(0.1) # Make sure to wait a small amount of time after disabling the muscle for messages to be sent
tf.endAll()

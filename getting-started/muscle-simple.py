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

node_net = tf.discover([105])[0]  # Discover networks over USB and get the first one

node_net.refreshDevices()  # Discover all Node devices on the selected network
time.sleep(1) # Wait for the devices to be discovered

node = node_net.node_list[0]  # Get the first connected Node

muscle = tf.Muscle(idnum = 0)  # Match idnum to the muscle port number 0=M1, 1=M2
node.setMuscle(0, muscle)  # Assign the muscle to the Node at port 0

# Move the Muscle
muscle.setMode("percent")
muscle.setSetpoint(0.1)
muscle.setEnable(True)

tf.delay(5)  # Increase if needed but be careful!  There is no safegaurd to prevent the muscle from overheating

muscle.disableAll()

time.sleep(1)
tf.endAll()


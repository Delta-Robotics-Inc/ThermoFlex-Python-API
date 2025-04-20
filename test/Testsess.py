'''
Test for ThermoFlex Session Logging
'''

import thermoflex as tf
import time as t
#write tests that send commands


network = tf.discover() #input the product id and returns a list of nodes available
node0 = network[0].self_node
network[0].refreshDevices()
muscle = tf.devices.Muscle
# Example of how to characaterize muscles. 
muscle1 = muscle(_port = 0, resist= 300, diam= 2, length= 150)
muscle2 = muscle(_port = 1, resist= 290, diam= 2, length= 145)

node0.attachMuscle(muscle1, 0) #takes the mosfet number muscle params to muscle
node0.attachMuscle(muscle2, 0)
node0.logstate["printlog"]=True
#node0.logstate["filelog"]=True #sets filelogging to true
node0.logstate["binarylog"]=True #sets the logpath and logging to true

t.sleep(0.1)
node0.status('compact')

m_to_train = muscle1  # Just set to the muscle port that should be trained

# Muscle setup
m_to_train.setMode("percent")  # Train mode does not work yet.  This is the best way for now until we meet and discuss how train mode will work.

m_to_train.setSetpoint(setpoint = 0.1)  # Dial this value in but start low!  Keep in mind that smoking should occur sometime near the end of the 50 seconds when this value is tuned in.

# Specify training program wait values


wait1 = 30
wait2 = 10


# Test Control Script
m_to_train.setEnable(True)
t.sleep(wait1)
node0.disableAll() # Disable all at end of program (or disable just m_to_train)
node0.setLogmode(0)
tf.endAll()

# This is a new feature, but it would create a plot like I created in my niti-train-program.py based on the data stored to this text file.  You can parse it to create the sensor data arrays and then plot using the exact same method I used in my script
#tf.plotting(output_path)

#tf.userinput()
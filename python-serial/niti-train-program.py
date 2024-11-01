import thermoflex as tf


nodelist = tf.discover([105]) #input the product id and returns a list of nodes available
network = nodelist[0]

node0 = network.nodenet[0] #selects the first node in the network


# Example of how to characaterize muscles. 
muscle1 = tf.muscle(idnum = 0, resist= 300, diam= 2, length= 150)
muscle2 = tf.muscle(idnum = 1, resist= 290, diam= 2, length= 145)

node0.setMuscle(0, muscle1) #takes the mosfet number muscle params to muscle
node0.setMuscle(1, muscle2)


node0.status('compact')


# Set output path and mode (Like Binary vs UTF-8)

#node0.logstate["filelog"]=True #sets the logpath and logging to true
node0.logstate["dictlog"]=True #sets the logpath and logging to true
#node0.logstate["printlog"]=True #sets the logpath and logging to true


m_to_train = muscle1  # Just set to the muscle port that should be trained

# Muscle setup
m_to_train.setMode("percent")  # Train mode does not work yet.  This is the best way for now until we meet and discuss how train mode will work.

m_to_train.setSetpoint(0.1)  # Dial this value in but start low!  Keep in mind that smoking should occur sometime near the end of the 50 seconds when this value is tuned in.

# Specify training program wait values
wait1 = 30
wait2 = 10

# Test Control Script
node0.setLogmode(2)  # Set the node to fast logmode
m_to_train.setEnable(True)
tf.update()
tf.delay(wait1)  # Internally calls tf.update() until a timer has surpassed 1.0 second
node0.disableAll() # Disable all at end of program (or disable just m_to_train)
tf.delay(wait2) # Continue collecting data until the end of program
node0.setLogmode(0)
tf.update()
tf.endAll() # Closes node devices (serial.close())


# This is a new feature, but it would create a plot like I created in my niti-train-program.py based on the data stored to this text file.  You can parse it to create the sensor data arrays and then plot using the exact same method I used in my script
#tf.plotting(output_path)
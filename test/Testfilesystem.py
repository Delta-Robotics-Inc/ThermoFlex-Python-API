import thermoflex as tf
import time as t
#discover network
networks = tf.discover([105])
net1 = networks[0]
#get nodes from network
# call this to get all nodes in network

net1.refreshDevices()
t.sleep(2)
#for x in net1.node_list: print(x.node_id)
node1 = net1.getDevice(net1.node_list[2].node_id)

# Get node 1 from node net by id
muscle = tf.devices.muscle

muscle1 = muscle(idnum = 0, resist= 300, diam= 2, length= 150)
muscle2 = muscle(idnum = 1, resist= 290, diam= 2, length= 145)
node1.setMuscle(0, muscle1) #takes the mosfet number muscle params to muscle
node1.setMuscle(1, muscle2)

node1.logstate['filelog'] = True
node1.logstate['binarylog'] = True
net1.sess.logstate['binarylog'] = True
net1.sess.logstate['filelog'] = True
# Print status dump
#print(node1.status("dump"))


#run nodes
m_to_train = muscle1  # Just set to the muscle port that should be trained

# Muscle setup
m_to_train.setMode("percent")  # Train mode does not work yet.  This is the best way for now until we meet and discuss how train mode will work.
m_to_train.setEnable(True)
tf.delay(10)
node1.disableAll()
m_to_train.setSetpoint(0.1)
# see node data


# add log data to file
import thermoflex as tf

nodenet_list = tf.discover([105]) #input the product id and returns a list of nodes available
nodenet = nodenet_list[0]
nodenet.refreshDevices() # call this to get all nodes in network
# Get node 1 and node 2 from node net by id
node1 = nodenet.getDevice([0x01, 0x02, 0x03])
node2 = nodenet.getDevice([0x04, 0x05, 0x06])

print(node1.status("dump")) # Print status dump
print(node2.status("compact"))

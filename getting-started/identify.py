# A simple script that checks for the presence of a ThermoFlex network and prints the Node IDs of the connected Nodes.
import thermoflex as tf
import time

node_net = tf.discover([105])[0]  # Discover networks over USB and get the first one

node_net.refreshDevices()  # Discover all Node devices on the selected network
time.sleep(1) # Wait for the devices to be discovered

print("Detected Nodes:")
for node in node_net.node_list:
    # Print the list of Nodes on the network in X.X.X syntax
    print(f'Node: {node.node_id[0]}.{node.node_id[1]}.{node.node_id[2]}')

time.sleep(1)
tf.endAll()
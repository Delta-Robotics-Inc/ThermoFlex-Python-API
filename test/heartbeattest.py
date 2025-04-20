import thermoflex as tf
from threading import Timer
import time as t
network = tf.discover()
tf.Debugger.ENABLED = False
net1 = network[0]
t.sleep(2)
print(network)
print(net1)
print(net1.node_list)

while True:
    for net in network:
        print(net1.node_list)
        t.sleep(4)
    
import thermoflex as tf
from threading import Timer
import time as t
network = tf.discover()
net1 = network[0]
while True:
    print(net1.node_list)
    t.sleep(4)
    
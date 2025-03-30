import thermoflex as tf
import time as t
import threading as thr


def threaded(func):
    global threadlist
    threadlist = []
    
    def wrapper(*args, **kwargs):
        thread = thr.Thread(target=func, args=args, kwargs = kwargs)
        thread.start()
        #print(thread.getName(),func) # prints thread name and function type
        threadlist.append(thread)
        return thread

    return wrapper


@threaded
def heartbeat(node):
    while True:
        node.status("compact")
        t.sleep(1)

network = tf.discover()
net1 = network[0]
Node = net1.self_node
tf.Debugger.TF_DEBUG_LEVEL = tf.tools.debug.DEBUG_LEVELS['WARNING']
heartbeat(Node)

while True:
    print(net1.node_list)
    print(Node.node_status)
    t.sleep(4)
    
for th in threadlist:
    th.join()
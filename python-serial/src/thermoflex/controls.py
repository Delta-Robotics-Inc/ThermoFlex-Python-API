

from .network import NodeNet
from .devices import Node, muscle
from .tools.nodeserial import stop_threads_flag, threaded
from .tools.debug import Debugger as D, DEBUG_LEVELS
import serial as s
import serial.tools.list_ports as stl
import time as t
import sys

prt = stl.comports(include_links=False)
prod = [105] # Product id list

#-----------------------------------------------------------------------------------------------------------

#TODO: put a rediscover in discover, have discover check for existing node serial numbers                         

def discover(proid = prod): 
    '''
    
    Takes node-object idnumber and tries to find corresponding port.
    
    '''
    
    ports = {}
    
    z = len(NodeNet.netlist)

    for por in prt:
        ports[por.pid]= [por.name, por.serial_number]    
        
    for p in proid:
        for key in ports.keys():
            if p == key:
                nodenetw = NodeNet(z+1, ports[key][0])
                #nodenetw.openPort()
                #nodenetw.closePort()
                z+=1
    if z == 0:
        raise ImportError('There are no connected nodes.')
    else:
        return NodeNet.netlist
     
#------------------------------------------------------------------------------------

@threaded
def timer(time):
    global timeleft
    timeleft = time
    for x in range(time):
        timeleft-=1
        t.sleep(1)
    stop_threads_flag.clear()


def updatenet(network:object): #choose which node to update and the delay
    '''
    
    Updates all nodes in the list to send commands and receive data
    
    '''  
    network.refreshDevices()
        
def delay(time):
    
    timer(time)
    while timeleft>0:
        for net in NodeNet.netlist:
            updatenet(net)
        

def endAll():
    '''
    
    Closes all node ports. and end all threads.
    
    '''

    stop_threads_flag.set() # End all threads by raising this flag

    # Wait for all threads to 
    # TODO either add more flags for each thread to end or find a way to signal in a different way
    while(stop_threads_flag.is_set()):
        pass

    D.debug(DEBUG_LEVELS['INFO'], "endAll", "All threads have been closed")
    
    for node in Node.nodel:
        try:
            node.net.closePort()
        except s.SerialException():
            D.debug(DEBUG_LEVELS['WARNING'], "endAll", "Warning: Port not open but attempted to close")
            pass
        finally:
            del node

    sys.exit() # End program -> change if program needs to continue

def userinput(): #TODO: add rest of inputs
    usr = input()
    if 'quit' in usr:
        sys.exit()

    
#----------------------------------------------------------------------------------------------------------------------------

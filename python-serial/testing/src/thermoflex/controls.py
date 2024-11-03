'''
Comments
'''
from .network import nodenet
from .devices import node, muscle
from .tools.packet import deconstructor
import serial as s
import threading as thr
import serial.tools.list_ports as stl
import pandas as pd
import time as t
import sys

prt = stl.comports(include_links=False)
prod = [105] # Product id list

def threaded(func):
    global threadlist
    threadlist = []
    def wrapper(*args, **kwargs):
        thread = thr.Thread(target=func, args=args, kwargs = kwargs)
        thread.start()
        threadlist.append(thread)
        return thread

    return wrapper

#-----------------------------------------------------------------------------------------------------------

#TODO: put a rediscover in discover, have discover check for existing node serial numbers                         

def discover(proid = prod): 
    '''
    
    Takes node-object idnumber and tries to find corresponding port.
    
    '''
    
    ports = {}
    
    z = len(nodenet.netlist)

    for por in prt:
        ports[por.pid]= [por.name, por.serial_number]    
        
    for p in proid:
        for key in ports.keys():
            if p == key:
                nodenetw = nodenet(z+1, ports[key][0])
                #nodenetw.openPort()
                #nodenetw.closePort()
                z+=1
    return nodenet.netlist
     
#------------------------------------------------------------------------------------

@threaded
def timer(time):
    global timeleft
    timeleft = time
    for x in range(time):
        timeleft-=1
        t.sleep(1)


def updatenet(network:object): #choose which node to update and the delay
    '''
    
    Updates all nodes in the list to send commands and receive data
    
    '''  
    network.refreshDevices()
        
def delay(time):
    
    timer(time)
    while timeleft>0:
        updatenet()
        

def endAll():
    '''
    
    Closes all node ports. and end all threads.
    
    '''
    
    for node in nodel:
        try:
            node.net.closePort()
        except s.SerialException():
            pass
        finally:
            del node

def userinput():
    usr = input()
    if 'quit' in usr:
        sys.exit()

    

    
#----------------------------------------------------------------------------------------------------------------------------
for th in threadlist:
        th.join()
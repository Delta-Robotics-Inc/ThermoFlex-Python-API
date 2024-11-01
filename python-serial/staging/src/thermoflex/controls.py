'''
Comments
'''
from .network import nodenet
from .devices import node, muscle
from .tools.packet import deconstructor
import threading as thr
import serial.tools.list_ports as stl
import pandas as pd
import time as t
import os

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

def discover_orig(proid = prod):  
    '''
   
    Takes a list of product id's and returns a list of Node-class objects.
    
    Parameters
    ---------
    proid : list
        DESCRIPTION. A list of int values that correspond with the producti id
   
    RETURNS
    ----------
    nodel: list
        DESCRIPTION. A list of the node objects with their idnumbers, ports, and product id as identifiers
    '''
    
    node.nodel = []
    ports = {}
    
    
    z = len(nodel)

    for por in prt:
        ports[por.serial_number]= por.name    
        
    for p in proid:
        for key in ports.keys():
            if p == key:
                nodeob = node(z+1, ports[key])
                nodeob.serial = key
                node.nodel.append(nodeob)
                print(nodel[z].port0)
                nodel[z].openPort()
                nodel[z].closePort()
                z+=1
    nodecount = len(node.nodel)
    return node.nodel
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
         
    for node in network.nodenet():
        node.update()
        if node.logstate['dictlog'] or node.logstate['printlog'] or node.logstate['filelog']or node.logstate['binarylog']== True:
            logTo(node,node.buffer,dt=1)
        node.lastcmd.clear()
        
def delay(time):
    
    timer(time)
    while timeleft>0:
        update()
        

def endAll():
    '''
    
    Closes all node ports. and end all threads.
    
    '''
    
    for node in nodel:
        node.net.closePort()
        del node

#----------------------------------------------------------------------------------------------------------------------------
for th in threadlist:
        th.join()
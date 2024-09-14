# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 12:38:45 2024

@author: School
"""
from .commands import *
#from .sessions import session
import threading as thr
import serial.tools.list_ports as stl
import pandas as pd
import time as t
import os

prt = stl.comports(include_links=False)
nodecount = 0
prod = [105] # Product id list
threadlist = []
sess_filepath = os.getcwd() #set base filepath


def threaded(func):
    
    
    def wrapper(*args, **kwargs):
        thread = thr.Thread(target=func, args=args, kwargs = kwargs)
        thread.start()
        threadlist.append(thread)
        return thread

    return wrapper

#-----------------------------------------------------------------------------------------------------------

def discover(proid = prod):  # Add to node list here
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
    global nodel, nodecount
    nodel = []
    ports = {}
    
    if nodecount==0:
        z = nodecount
    else:
        z = nodecount-1

    for por in prt:
        ports[por.pid]=por.name    
        
    for p in proid:
        for key in ports.keys():
            if p == key:
                nodeob = node(z+1,ports[key],key)
                nodel.append(nodeob)
                print(nodel[z].port0)
                nodel[z].openPort()
                nodel[z].closePort()
                z+=1
    nodecount = len(nodel)
    return nodel
                         
def rediscover(idn): #id number
    '''
    
    Takes node-object idnumber and tries to find corresponding port.
    
    '''
    ports = {}
    
    for por in prt:
        ports[por.pid]=por.name
    for n in nodel:
        if nodel[n].prodid == idn:
            nodel[n].port0 = ports[idn] 
 
    #TODO Later: use serial numbers to track individual devices   

#------------------------------------------------------------------------------------

@threaded
def timer(time):
    global timeleft
    timeleft = time
    for x in range(time):
        timeleft-=1
        t.sleep(1)

#Thread the update and delay functions?
def update(): #choose which node to update and the delay
    '''
    
    Updates all nodes in the list to send commands and receive data
    
    '''
         
    for node in nodel:
        node.update()
        if node.logstate['dictlog'] or node.logstate['printlog'] or node.logstate['filelog']== True:
            logTo(node,node.buffer)
        
def delay(time):
    
    timer(time)
    while timeleft>0:
        update()
        

def endAll():
    '''
    
    Closes all node ports. and end all threads.
    
    '''
    
    for node in nodel:
        node.closePort()

@threaded
def logTo(node:object, logdata):
    '''
    
    Sends log data to terminal output, directory or file.
    Writes log data to a file.
    
    '''
    filepath = sess_filepath + f'\logs\node{node.idnum}logdata'
    
    logdata = logdata.decode("utf-8").strip()
    
    nodelist = list(node.nodedict.keys())
    m1list = list(node.m1dict.keys())
    m2list = list(node.m2dict.keys())
    nodedict2 = node.nodedict.copy()
    m1dict2 = node.m1dict.copy()
    m2dict2 = node.m2dict.copy()
    
    try:
        logdata  # Properly decode and strip the data
        if not logdata:
            pass #does nothing statement upon being empty

        else:   
            try: 
                
                splitbuff = logdata.split(' ')
                splitnode = splitbuff[:splitbuff.index('M1')]
                splitm1 = splitbuff[splitbuff.index('M1') + 1:splitbuff.index('M2')]
                splitm2 = splitbuff[splitbuff.index('M2') + 1:]
            
                if node.logstate['dictlog'] == True: #checks log data         
                    
                    for x in nodelist:
                        if x == 'A' or x == 'C':
                            node.nodedict[x].append(int(splitnode[nodelist.index(x)]))
                        elif x == 'B' or x == 'D':
                            node.nodedict[x].append(float(splitnode[nodelist.index(x)]))
        
                    for x in m1list:
                        if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                            node.m1dict[x].append(int(splitm1[m1list.index(x)]))
                        else:    
                            node.m1dict[x].append(float(splitm1[m1list.index(x)]))
        
                    for x in m2list:
                        if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                            node.m2dict[x].append(int(splitm2[m2list.index(x)]))
                        else:
                            node.m2dict[x].append(float(splitm2[m2list.index(x)]))
                            
                if node.logstate['printlog'] == True:
                    print(str(logdata))
                
                if node.logstate['filelog'] == True: 
                    
                    for x in nodelist: 
                        if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                            nodedict2[x] = int(splitnode[nodelist.index(x)])
                        else:
                            nodedict2[x] = float(splitnode[nodelist.index(x)])
                    
                    for x in m1list:
                        if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                            m1dict2[x] = int(splitm1[m1list.index(x)])
                        else:
                            m1dict2[x] = float(splitm1[m1list.index(x)])
                    
                    for x in m2list:
                        if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                            m2dict2[x] = int(splitm2[m2list.index(x)])
                        else:
                            m2dict2[x] = float(splitm2[m2list.index(x)])
                        #pandas write to .csv
                        
                    pd.DataFrame(nodedict2).to_csv(path = filepath + '\node.csv', mode = 'a')
                    pd.DataFrame(m1dict2).to_csv(path = filepath + '\M1.csv', mode = 'a')
                    pd.DataFrame(m2dict2).to_csv(path = filepath + '\M2.csv', mode = 'a')
            
            except IndexError:
                pass
            except ValueError:
                pass  

    finally:
        pass

#----------------------------------------------------------------------------------------------------------------------------
for th in threadlist:
        th.join()
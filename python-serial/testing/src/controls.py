'''
Comments
'''

from .devices import *
from .tools.packet import deconstructor
import threading as thr
import serial.tools.list_ports as stl
import pandas as pd
import time as t
import os

prt = stl.comports(include_links=False)
prod = [105] # Product id list
sess_filepath = os.getcwd().replace("\\","/") #set base filepath


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
                nodenetw.openPort()
                nodenetw.closePort()
                z+=1
    return nodenet.netlist()
 
       

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

@threaded
def logTo(node:object, logdata, dt:int):
    '''
    
    Sends log data to terminal output, directory or file.
    Writes log data to a file.
    
    '''
    filepath = sess_filepath + f'\logs\node{node.idnum}logdata'
    
    
    
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
            readlog = deconstructor(logdata)
            try: 
                if dt == 1:
                    splitbuff = readlog.split(' ')
                    splitnode = splitbuff[:splitbuff.index('M1')]
                    splitm1 = splitbuff[splitbuff.index('M1') + 1:splitbuff.index('M2')]
                    splitm2 = splitbuff[splitbuff.index('M2') + 1:]
                
                    if node.logstate['printlog'] == True:
                        print(str(readlog))
                    
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
                                
                    if node.logstate['binarylog'] == True:
                        with open('{filepath}\binary\logdata.ses', 'a') as f:
                            f.write(logdata)
                    
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
            
                elif dt == 0:
                    if node.logstate['printlog'] == True:
                        print(str(readlog))
                    if node.logstate['binarylog'] == True:
                        with open(f'{filepath}\binary\logdata.ses', 'a') as f:
                            f.write(logdata)
                    if node.logstate['dictlog'] == True:
                        pass
                    if node.logstate['filelog'] == True:
                        with open(f'{filepath}\sendlog.txt', 'wt') as f:
                            f.write(readlog)
            except IndexError:
                pass
            except ValueError:
                pass  

    finally:
        pass

#----------------------------------------------------------------------------------------------------------------------------
for th in threadlist:
        th.join()
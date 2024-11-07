'''
Comments
'''
import threading as thr
import multiprocessing as mp
import os
import shutil as sh
from .tools.packet import deconst_response_packet
base_path = os.getcwd().replace("\\","/") + '/ThermoflexSessions' #set base filepath
sess_filepath = os.getcwd().replace("\\","/") #new directory filepath

#TODO filepaths of installing scripts
threadlist = []
def threaded(func):
    global threadlist
    
    def wrapper(*args, **kwargs):
        thread = thr.Thread(target=func, args=args, kwargs = kwargs)
        thread.start()
        threadlist.append(thread)
        return thread

    return wrapper
#TODO: logger class; wraps short and long term logging;
# Pandas rolling buffer of recent data and file logging of current data
def logTo(node:object, logdata, dt:int): #TODO: reformat log
    '''
    
    Sends log data to terminal output, directory or file.
    Writes log data to a file.
    
    '''
    filepath = sess_filepath + f'/logs/logdata'
    
    
    try:
        logdata  # Properly decode and strip the data
        if not logdata:
            pass #does nothing statement upon being empty

        else:   
            
            try: #deconstruct and use data to log
                if dt == 0:
                    readlog = deconst_response_packet(logdata)
                    response_type = readlog[0]
                    response_data = readlog[1]
                
                    if node.logstate['printlog'] == True:
                       for res in response_data.keys():
                           print(f'{res}: {response_data[res]}')
                    
                    if node.logstate['dictlog'] == True: #checks log data         
                        if response_type == 'general':
                            pass
                        elif response_type == 'status':
                            for value in response_data.keys():
                                node.data_dict[value].append(response_data[value])
                                
                    if node.logstate['binarylog'] == True:
                        with open('{filepath}/binary/logdata.ses', 'a') as f:
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
            
                elif dt == 1:
                    readlog = logdata
                    if node.logstate['printlog'] == True:
                        print(str(readlog))
                    if node.logstate['binarylog'] == True:
                        with open(f'{filepath}/binary/logdata.ses', 'a') as f:
                            f.write(logdata)
                    if node.logstate['dictlog'] == True:
                        pass
                    if node.logstate['filelog'] == True:
                        with open(f'{filepath}/sendlog.txt', 'wt') as f:
                            f.write(readlog)
            except IndexError:
                pass
            except ValueError:
                pass  

    finally:
        pass

class session(): 
    sessionl = []
    sescount = len(sessionl)    
    
    def __init__(self, network,iden = sescount+1): 
        
        self.id = iden
        session.sessionl.append(self)
        self.networks = []
        self.networks.append(network)
        self.environment = None #setup by launch; path dir string
        self.launch()
        
    def launch(self): #opens all files and folders for sessions
        self.environment = f'{base_path}/session{self.id}'
        try:
            fpath = os.path.exists(self.environment)
            #print(fpath) #DEBUG
            if fpath == False:
                
                self.setlogpath()
 
        finally:
            
            os.chdir(self.environment)
    
    def end(self): #ends the session
        
        sh.copytree(f'{self.environment}/logs' , f'{base_path}/session{self.id}log', dirs_exist_ok = True)
        os.remove(self.environment)
        self.connode.closePort()
    
    def logging(self,cmd,tp): #logs the session
        #print(cmd,tp)   #DEBUG
        if tp == 0:
            for net in self.networks:
                for node in net.node_list:
                    # print(f'Attempt to Log Node ID: {node.node_id}')
                    # print(f"Node ID from Command to Log: {cmd['sender_id']}")
                    if cmd['sender_id'] == node.node_id:
                        print(f"Node: {node}", f"CMD: {cmd['payload']}", f"tp: {tp}")
                        print("Logging...")
                        logTo(node, cmd['payload'], tp)
        elif tp == 1:
            logTo(cmd.destnode,cmd.construct,tp)
                
    def setlogpath(self): #creates logpath
        
        BINARYDATA = f'{self.environment}/logs/logdata/binary/logdata.ses'
        try:
            os.makedirs(f'{self.environment}/logs/logdata/binary')
        except FileExistsError:
            pass
        finally:
            with open(BINARYDATA, 'xb') as f:
                pass         
            
def endsession(session:object):
    session.end()
    del session
            

for th in threadlist:
        th.join()


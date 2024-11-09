'''
Comments
'''
import threading as thr
from sys import getsizeof as getsize
import os
import shutil as sh
from .tools.packet import deconst_response_packet, DATATYPE
from .tools.debug import debug
from .devices import Node
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
class Logger():
    def __init__(self,session):
        self.session = session
        self.location = session.environment
        self.local = []

    def rollinglog(self, data): #adds data to local rolling buffer 
        self.local.append(data)
        if getsize(self.local) > 512000000: #checks data size isnt greater than 512Mb
            self.local.pop(0)

    def filelog(node:object, logdata, dt:int): #log Format: Time, log type, message
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
                                f.write(response_data)

                    elif dt == 1:
                        readlog = logdata
                        if node.logstate['printlog'] == True:
                            print(str(readlog))
                        if node.logstate['binarylog'] == True:
                            with open(f'{filepath}/binary/logdata.ses', 'ab') as f:
                                f.write(logdata)
                        if node.logstate['dictlog'] == True:
                            pass
                    
                    else:
                        readlog = logdata
                    
                except IndexError:
                    pass
                except ValueError:
                    pass  

        finally:
            pass
    
    def logging(self, message): #takes session log data and sends to log
            
        if not message.message_location:
            self.filelog(message)
        else:
            self.filelog(message)
            self.rollinglog(message)
    
class Session(): 
    sessionl = []
    sescount = len(sessionl)    
    debug_node = Node('DEBUG')
    debug_node.node_id = 'DEBUG'
    def __init__(self, network,iden = sescount+1): 
        self.id = iden
        Session.sessionl.append(self)
        self.networks = []
        self.networks.append(network)
        self.logger = Logger(self)
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
    
    def logging(self,cmd): #logs the session
        #print(cmd,tp)   #DEBUG
        self.logger.logging(cmd)
                
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


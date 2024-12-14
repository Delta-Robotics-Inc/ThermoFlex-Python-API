'''
Comments
'''
from sys import getsizeof as getsize
import os
import shutil as sh
from datetime import datetime as dt
from .tools.nodeserial import threaded, stop_threads_flag
from .tools.packet import deconst_serial_response, DATATYPE, LogMessage
from .tools.debug import Debugger as D, DEBUG_LEVELS
from .devices import Node
base_path = os.getcwd().replace("\\","/") + '/ThermoflexSessions' #set base filepath
sess_filepath = os.getcwd().replace("\\","/") #new directory filepath

#TODO: logger class; wraps short and long term logging;
# Pandas rolling buffer of recent data and file logging of current data
class Logger:
    def __init__(self,session):
        self.session = session
        self.location = session.environment
        self.local = []

    def rollinglog(self, data:tuple): #adds data to local rolling buffer 
        self.local.append(data)
        if getsize(self.local) > 512000000: #checks data size isnt greater than 512Mb
            self.local.pop(0)

    @threaded
    def filelog(self,logmsg): #lo/;pgsg Format: Time, log type, message
        '''
        
        Sends log data to terminal output, directory or file.
        Writes log data to a file.
        
        '''
        filepath = self.location + '/logs/logdata'
        timeparse = dt.now()
        mil = lambda x:int(x)//1000
        logtime = f'{timeparse.month}/{timeparse.day}/{timeparse.year} {timeparse.hour}:{timeparse.minute}:{timeparse.second}.{mil(timeparse.microsecond)}'

        #t.strftime('%x %X') #time from epoch measure
        try:
            logmsg  # Properly decode and strip the data
            if not logmsg:
                pass #does nothing statement upon being empty

            else:   

                try: #checks the data type and returns the log string
                
                    readlog = f'{logtime} {logmsg.message_type} {logmsg.message_address} {logmsg.generated_message}'    
               
                    node = None
                    if not logmsg.message_address == 0: # checks for sender id    
                        for nood in Node.nodel:
                            if nood.node_id == logmsg.message_address:
                                node = nood
                        
                    if node:
                        if node.logstate['printlog'] == True:
                            print(readlog)

                        if node.logstate['binarylog'] == True:
                            with open(f'{filepath}/logdata.ses', 'ab') as f:
                                f.write(bytes(readlog+'\n','ascii'))
                        
                        if node.logstate['filelog'] == True:
                            with open(f'{filepath}/logdata.txt', 'a') as f:
                                f.write(readlog+'\n')
                    else:
                        if self.session.logstate['printlog'] == True:
                            print(readlog)

                        if self.session.logstate['binarylog'] == True:
                            with open(f'{filepath}/logdata.ses', 'ab') as f:
                                f.write(bytes(readlog+'\n','ascii'))
                        
                        if self.session.logstate['filelog'] == True:
                            with open(f'{filepath}/logdata.txt', 'a') as f:
                                f.write(readlog+'\n')

                except IndexError:
                    pass
                except ValueError:
                    pass  

        finally:
            stop_threads_flag.clear()
    
    def logging(self, message:LogMessage): #takes session log data and sends to log
            
        self.filelog(message)
        self.rollinglog((message.message_type, message.generated_message)) #creates a tuple with the log type and message

class Session: 
    sessionl = []
    sescount = len(sessionl)    
    # debug_node = Node('DEBUG')
    # debug_node.node_id = 'DEBUG'
    
    def __init__(self, network,iden = sescount+1): 
        self.id = iden
        Session.sessionl.append(self)
        self.networks = []
        self.networks.append(network)
        self.logstate = {'binarylog':False, 'printlog':False, 'filelog':False}
        self.environment = None #setup by launch; path dir string
        self.launch()
        self.logger = Logger(self)
        D.DEBUG_SESSION = self
    
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
    
    def logging(self,cmd, logtype:int): #creates the LogMessage object with the available log data
        #print(cmd,tp)   #DEBUG
        logmsg = None
        if logtype == 0:
            logmsg = LogMessage('SENT',cmd.construct)
            sender_id_int = int.from_bytes(cmd.destnode.node_id, byteorder='big')
            logmsg.message_address = sender_id_int
        elif logtype == 1:
            logmsg = LogMessage('RECEIVED', cmd['payload']) # creates log message object
            sender_id_int = int.from_bytes(cmd['sender_id'], byteorder='big')
            logmsg.message_address = sender_id_int
        elif logtype == 2:
            sender_id_int = 0 #int.from_bytes(cmd['sender_id'], byteorder='big')
            logmsg = LogMessage('SERIAL_DEBUG', cmd)
            logmsg.message_address = sender_id_int
        elif logtype == 3:
            logmsg = LogMessage(cmd[0],cmd[1]) #for DEBUG LOGGING
        else:
            raise BaseException('Unknown log type')
        
        self.logger.logging(logmsg)
            
                
    def setlogpath(self): #creates logpath
        
        BINARYDATA = f'{self.environment}/logs/logdata/logdata.ses'
        FILEDATA = f'{self.environment}/logs/logdata/logdata.txt'
        try:
            os.makedirs(f'{self.environment}/logs/logdata')
        except FileExistsError:
            pass
        finally:
            with open(BINARYDATA, 'xb') as f:
                pass         
            with open(FILEDATA, 'xt') as f:
                pass
            

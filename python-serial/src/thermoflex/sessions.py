'''
Add shutoff switch
'''
from sys import getsizeof as getsize
import os
import shutil as sh
from datetime import datetime as dt
from .tools.thread_manager import thread_manager, stop_threads_flag
from .tools.packet import deconst_serial_response, DATATYPE, LogMessage
from .tools.debug import Debugger as D, DEBUG_LEVELS
import time as t

base_path = os.getcwd().replace("\\","/") + '/ThermoflexSessions' #set base filepath
sess_filepath = os.getcwd().replace("\\","/") #new directory filepath

class Logger:
    '''
    Logger class; wraps short and long term logging;
    Pandas rolling buffer of recent data and file logging of current data
    '''
    def __init__(self,session):
        self.session = session
        self.location = session.environment
        self.local = []
        self.log_interval = 1.0  # Default log interval in seconds
        self.logfile = None
        self._filelog_thread = None
        self._shutdown_requested = False

    def rollinglog(self, data:tuple): #adds data to local rolling buffer 
        self.local.append(data)
        if getsize(self.local) > 512000000: #checks data size isnt greater than 512Mb
            self.local.pop(0)

    def start_file_logging(self):
        """Start the file logging thread"""
        if self._filelog_thread and self._filelog_thread.is_alive():
            D.debug(DEBUG_LEVELS['WARNING'], "Session", "File logging thread already running")
            return
        
        self._shutdown_requested = False
        self._filelog_thread = thread_manager.create_thread(
            target=self.filelog,
            name=f"filelog_{self.session.id}",
            shutdown_timeout=3.0
        )
        D.debug(DEBUG_LEVELS['INFO'], "Session", f"Started file logging thread for session {self.session.id}")

    def stop_file_logging(self, timeout=3.0):
        """Stop the file logging thread gracefully"""
        if not self._filelog_thread:
            return True
        
        D.debug(DEBUG_LEVELS['INFO'], "Session", f"Stopping file logging for session {self.session.id}")
        self._shutdown_requested = True
        
        success = self._filelog_thread.stop(timeout=timeout)
        if success:
            D.debug(DEBUG_LEVELS['INFO'], "Session", "File logging stopped successfully")
        else:
            D.debug(DEBUG_LEVELS['WARNING'], "Session", "File logging did not stop gracefully")
        
        self._filelog_thread = None
        return success

    def filelog(self, stop_event=None):
        """
        Log node data to file
        
        Args:
            stop_event: Threading event to signal thread shutdown (injected by ThreadManager)
        """
        # Use provided stop_event or fall back to instance shutdown flag
        def should_stop():
            return (stop_event and stop_event.is_set()) or self._shutdown_requested or stop_threads_flag.is_set()

        # Initialize log file
        filepath = self.location + '/logs/logdata/logdata.txt'
        try:
            self.logfile = open(filepath, 'a')
            D.debug(DEBUG_LEVELS['INFO'], "Session", f"Opened log file: {filepath}")
        except Exception as e:
            D.debug(DEBUG_LEVELS['ERROR'], "Session", f"Failed to open log file: {e}")
            return

        try:
            while not should_stop():
                try:
                    # Get all active nodes from all networks in the session
                    active_nodes = []
                    for network in self.session.networks:
                        if hasattr(network, 'get_all_nodes'):
                            active_nodes.extend(network.get_all_nodes())
                    
                    # Log data for each active node
                    for node in active_nodes:
                        if hasattr(node, 'logstate') and node.logstate.get('filelog', False):
                            # Get node status
                            status = node.getStatus() if hasattr(node, 'getStatus') else None
                            if status:
                                # Log node status
                                self.logfile.write(f"{t.time()},{node.id},{status}\n")
                                
                                # Log muscle status if available
                                if hasattr(node, 'muscles') and node.muscles:
                                    for muscle in node.muscles.values():
                                        if hasattr(muscle, 'SMA_status') and muscle.SMA_status:
                                            muscle_status = muscle.muscleStatus() if hasattr(muscle, 'muscleStatus') else None
                                            if muscle_status:
                                                self.logfile.write(f"{t.time()},{node.id},muscle{muscle.portNum},{muscle_status}\n")
                    
                    if self.logfile:
                        self.logfile.flush()  # Ensure data is written to disk
                    
                    # Sleep with frequent shutdown checks
                    sleep_time = self.log_interval
                    check_interval = 0.1
                    while sleep_time > 0 and not should_stop():
                        t.sleep(min(check_interval, sleep_time))
                        sleep_time -= check_interval
                    
                except Exception as e:
                    D.debug(DEBUG_LEVELS['ERROR'], "Session", f"Error in file logging: {e}")
                    if should_stop():
                        break
                    t.sleep(1.0)  # Wait a bit before retrying
        
        finally:
            # Close log file when thread ends
            if self.logfile:
                self.logfile.close()
                D.debug(DEBUG_LEVELS['INFO'], "Session", f"Closed log file for session {self.session.id}")

    def logging(self, message:LogMessage): #takes session log data and sends to log
        self.rollinglog((message.message_type, message.generated_message)) #creates a tuple with the log type and message

class Session: 
    sessionl = []
    sescount = len(sessionl)    
    # debug_node = Node('DEBUG')
    # debug_node.id = 'DEBUG'
    
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
    
    def enable_file_logging(self):
        """Enable file logging and start the logging thread"""
        self.logstate['filelog'] = True
        self.logger.start_file_logging()
        D.debug(DEBUG_LEVELS['INFO'], "Session", f"File logging enabled for session {self.id}")
    
    def disable_file_logging(self):
        """Disable file logging and stop the logging thread"""
        self.logstate['filelog'] = False
        success = self.logger.stop_file_logging()
        if success:
            D.debug(DEBUG_LEVELS['INFO'], "Session", f"File logging disabled for session {self.id}")
        else:
            D.debug(DEBUG_LEVELS['WARNING'], "Session", f"File logging shutdown incomplete for session {self.id}")
        return success
    
    def launch(self): #opens all files and folders for sessions
        self.environment = f'{base_path}/session{self.id}'
        try:
            fpath = os.path.exists(self.environment)
            #print(fpath) #DEBUG
            if fpath == False:
                self.setlogpath()

            os.chdir(self.environment)
        except:
            print("Session launch failed")
            Session.sessionl.remove(self)
            del self
            return    
            
    def end(self): #ends the session
        """End the session and clean up all resources"""
        D.debug(DEBUG_LEVELS['INFO'], "Session", f"Ending session {self.id}")
        
        # Stop file logging first
        if self.logstate.get('filelog', False):
            self.disable_file_logging()
        
        # Clean up session files
        try:
            sh.copytree(f'{self.environment}/logs' , f'{base_path}/session{self.id}log', dirs_exist_ok = True)
            sh.rmtree(self.environment)
            print(f'Session log saved to {base_path}/session{self.id}log')
        except PermissionError:
            print('Permission Error: Cannot remove session directory')
        except FileNotFoundError:
            print('FileNotFoundError: Session directory not found and cannot be saved')
        except Exception as e:
            print(f'Error: {e}')
            raise
        
        # Remove from session list
        if self in Session.sessionl:
            Session.sessionl.remove(self)
        
        D.debug(DEBUG_LEVELS['INFO'], "Session", f"Session {self.id} ended successfully")
    
    def logging(self,cmd, logtype:int): #creates the LogMessage object with the available log data
        #print(cmd,tp)   #DEBUG
        logmsg = None
        if logtype == 0:
            logmsg = LogMessage('SENT',cmd.construct)
            sender_id_int = int.from_bytes(cmd.destnode.id, byteorder='big')
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
            

'''
Comments
'''
#TODO: add status parsing

import time as t
from threading import Event
from .tools.packet import command_t
from .tools.nodeserial import send_command, send_command_str
from .tools.debug import Debugger as D, DEBUG_LEVELS

#arduino commands

SE = "set-enable"
RESET = "reset"
SM = "set-mode"
SS = "set-setpoint"
ST = "status"
STOP = "stop"
LOGMODE = "log-mode"
PERCENT = "percent"
AMP = "amps"
VOLT = "volts"
DEG =  "degree"


def enforce_size_limit(data:list,size = 100):
    if len(data) > size:
        data.pop(-1)

#---------------------------------------------------------------------------------------

class Node:
    """
    Device interface class for Thermoflex nodes.
    
    The Node class represents a single Thermoflex device on the network and provides
    the interface for controlling and monitoring the device. It handles all device-level
    operations including:
    - Device control and status monitoring
    - Muscle management and control
    - Device state tracking
    - Command generation and buffering
    
    The class maintains the device's state including:
    - Device identification and status
    - Connected muscles and their states
    - Control modes and setpoints
    - Heartbeat and communication status
    
    Device Control:
        - Status monitoring and reporting
        - Mode and setpoint control
        - Muscle enable/disable control
        - Device reset and configuration
        
    Muscle Management:
        - Muscle attachment and configuration
        - Muscle state tracking
        - Muscle control and monitoring
        - Muscle status reporting
        
    State Management:
        - Device status tracking
        - Heartbeat monitoring
        - Communication state
        - Error tracking and reporting
        
    The Node class is designed to be a pure device interface, with all network
    management handled by the NodeNet class. It focuses on providing a clean API
    for device control and monitoring.
    """
    def __init__(self, i, network=None, mosports:int = 2, n_id = [0x00, 0x00, 0x00], pulse = True):
        self.index = i
        self.net = network
        self.arduino = self.net.arduino if network else None
        self.logmode = 0
        self.id : list[int] = n_id
        self.canid = None
        self.firmware = None
        self.board_version = None
        self.node_status = {'uptime':None, 'errors':[],'volt_supply':None,'pot_values':None,'log_interval':None,'vrd_scalar':None,'vrd_offset':None,'max_current':None,'min_v_supply':None}
        self.mosports = mosports
        self.muscles = {}
        self.logstate = {'printlog':False, 'binarylog':False, 'filelog': False}
        self.status_curr = None
        self.latest_resp = None
        self.bufflist = []
        self.lastcmnd = None

        # Make default muscles
        self.muscle0 = Muscle(0, self)
        self.muscle1 = Muscle(1, self)
        self.muscles = {"0":self.muscle0, "1":self.muscle1}

        # Heartbeat system
        self.last_heartbeat_received = None  # Timestamp of last heartbeat received from node
        self.last_heartbeat_sent = None      # Timestamp of last heartbeat sent to node
        self.heartbeat_timeout = 5.0         # Timeout in seconds before node is considered inactive
        self.is_active = True                # Flag to track if node is currently active
        self.missed_heartbeats = 0           # Counter for missed heartbeats
        self.max_missed_heartbeats = 3       # Maximum allowed missed heartbeats before marking as inactive

        # Message tracking
        self.msgsent = False  # Flag to track if a message was sent to this node
        self.msgrec = True    # Flag to track if a message was received from this node
        if pulse == True:
            # Initialize heartbeat system for this node
            self.heartbeat = True  # Enable heartbeat monitoring for this node
            # Create a heartbeat command that will be sent periodically
            self.pulse = command_t(self, name = "heartbeat", params = [])
            # Timestamps for tracking last message sent/received
            self.tlastmsgrec = None  # Time of last message received from node
            self.tlastmsgsent = None # Time of last message sent to node

    def update_heartbeat(self, received=True):
        """Update heartbeat timestamps and status"""
        current_time = t.time()
        if received:
            self.last_heartbeat_received = current_time
            self.missed_heartbeats = 0
        else:
            self.last_heartbeat_sent = current_time

    def check_heartbeat_status(self) -> bool:
        """Check if node has missed heartbeats"""
        if not self.is_active:
            return False

        current_time = t.time()
        if self.last_heartbeat_received is None:
            return True  # Node hasn't sent any heartbeats yet

        time_since_last = current_time - self.last_heartbeat_received
        if time_since_last > self.heartbeat_timeout:
            self.missed_heartbeats += 1
            if self.missed_heartbeats >= self.max_missed_heartbeats:
                return False
        return True

    def deactivate(self):
        """Mark node as inactive"""
        if self.is_active:
            self.is_active = False
            self.disableAll()  # Disable all muscles when deactivating
            D.debug(DEBUG_LEVELS['WARNING'], "Node", f"Node {self.id} marked as inactive after {self.missed_heartbeats} missed heartbeats")

    def reactivate(self):
        """Reactivate a previously inactive node"""
        self.is_active = True
        self.missed_heartbeats = 0
        self.last_heartbeat_received = t.time()
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id} reactivated")

    def cleanup(self):
        """Clean up node resources"""
        self.disableAll()  # Ensure all muscles are disabled
        for m in self.muscles.values():
            m.cleanup()
        self.muscles.clear()
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id} cleaned up")

    def testMuscles(self, sendformat:int = 1):
        '''
        
        Tests the node and muscle connections. Send format takes integer; 0 for ascii, 1 for string format

        '''          
        
        # Port is already open in network, no need to open it again
        mode = command_t.modedef.index('percent')
        if sendformat == 1:
            send_command_str(command_t(self,"set-setpoint", [mode ,0.5], device = "m1"),self.net) # make own test command
            send_command_str(command_t(self,"set-setpoint", [mode ,0.5], device = "m2"),self.net)        
            #send_command_str(command_t(self, "log-mode", [1],device = "all"),self.net)
            #self.logmode = 1
          
            send_command_str(command_t(self, "set-enable", [True], device = "m1"),self.net)
            t.sleep(3.0)
           
            
            send_command_str(command_t(self, "set-enable", [False], device = "m1"),self.net)
            t.sleep(3.0)
           
           
            send_command_str(command_t(self, "set-enable", [True], device = "m2"),self.net)
            t.sleep(3.0)
          
            
            send_command_str(command_t(self, "set-enable", [False], device = "m2"),self.net)
            t.sleep(3.0)
          
            #send_command_str(command_t(self, "log-mode", [0],device = "all"),self.net)
            #self.logmode = 0
            print("Test complete")
        
        elif sendformat == 0:
            
            send_command(command_t(self,"set-setpoint", [mode ,0.5], device = "m1"),self.net) # make own test command
            send_command(command_t(self,"set-setpoint", [mode ,0.5], device = "m2"),self.net)        
            #send_command(command_t(self, "log-mode", [1],device = "all"),self.net)
            #self.logmode = 1
          
            send_command(command_t(self,"set-enable", [True], device = "m1"),self.net)
            t.sleep(3.0)
           
            
            send_command(command_t(self, "set-enable", [False], device = "m1"),self.net)
            t.sleep(3.0)
           
           
            send_command(command_t(self, "set-enable", [True], device = "m2"),self.net)
            t.sleep(3.0)
          
            
            send_command(command_t(self, "set-enable", [False], device = "m2"),self.net)
            t.sleep(3.0)
          
            #send_command(command_t(self, "log-mode", [0],device = "all"),self.net)
            #self.logmode = 0
            print("Test complete")

    def status(self, type):
        """Request and collect status from the device"""
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Requesting {type} status")
        
        if type == 'dump':
            status = command_t(self, name = 'status', params = [2])
            self.net.command_buff.append(status)
            D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Added dump status request to command buffer")
            t.sleep(0.5)
            return self.status_curr
        elif type == 'compact':
            status = command_t(self, name = 'status', params = [1])
            self.net.command_buff.append(status)
            D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Added compact status request to command buffer")
            t.sleep(0.5)
            return self.status_curr
        else:
            D.debug(DEBUG_LEVELS['WARNING'], "Node", f"Node {self.id}: Unknown status type '{type}'")
            return None

    def getStatus(self):
        """Get the current cached status"""
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Getting cached status: {self.status_curr}")
        return self.status_curr
    
    def updateStatus(self, inc_data):
        """Update node status from received data"""
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Updating status with data: {inc_data}")
        
        resp_type, resp_data = inc_data
        resp_type = resp_type.split(' ')
        
        if resp_type[1] == 'node':
            D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Processing node status update")
            for key in self.node_status.keys():
                try:
                    if key == 'errors':
                        self.node_status[key].insert(0,resp_data[key])
                        enforce_size_limit(self.node_status[key])
                    else:
                        self.node_status[key] = resp_data[key]
                except KeyError:
                    continue
            if resp_type[2] == 'dump':
                self.canid, self.firmware, self.board_version = resp_data['can_id'], resp_data['firmware'], resp_data['board_ver'] 
                if resp_data['muscle_count'] != len(self.muscles):
                    D.debug(DEBUG_LEVELS['WARNING'], 'StatusCheck', 'Number of muscles intialized does not match the number of muscles attached to Node.')
        
        elif resp_type[1] == 'SMA':
            D.debug(DEBUG_LEVELS['DEBUG'], 'updateStatus', f'Dispersing Muscle{resp_type[3]} status')
            for musc in self.muscles.values():
                if musc.mosfetnum == resp_type[3]:
                    for key in musc.SMA_status.keys():
                        try:
                            resp_data[key]
                            if type(musc.SMA_status[key]) == list:
                                musc.SMA_status[key].insert(0,resp_data[key])
                                enforce_size_limit(musc.SMA_status[key])
                            else:
                                musc.SMA_status[key] = resp_data[key]
                        except KeyError:
                            continue
                        
                    musc.enable_status = resp_data['enable_status']
                    musc.cmode = command_t.modedef[resp_data['dev']]
                    musc.train_state = resp_data['trainstate']
                    break
                else:
                    D.debug(DEBUG_LEVELS['ERROR'], 'updateStatus(muscle)', 'Unknown muscle mosport received.')
        else:
            D.debug(DEBUG_LEVELS['ERROR'], 'updateStatus', f'Incompatible status type: {resp_type}')
            
        # Update the status string
        status_str = str(self.node_status).replace('{','').replace('}','').replace("'",'')
        self.status_curr = f'Node{self.index}, Address:{self.id}, Firmware:{self.firmware}, Board version:{self.board_version}, {status_str}'
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Updated status_curr: {self.status_curr}")

    def reset(self, device = "node"):
        """Send reset command to the node"""
        reset = command_t(self, name = 'reset', params = [], device = device)
        self.net.command_buff.append(reset)

    def setLogmode(self, mode:int):
        """Set the log status of the node"""
        self.logmode = mode
        command = command_t(self, name = LOGMODE, device = "all", params = [mode])
        self.net.command_buff.append(command)

    def setMode(self, conmode, device = 'all'):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id}: Setting mode for port {device} to {conmode}")
        '''
        
        Sets the data mode that the muscle will recieve. identify muscles by dictionary key.
        
        '''
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id}: Setting mode for port {device} to {conmode}")

        # TODO wrap the following code into a function "identifyControlMode()" and replace in other methods
        cmode = None
        if conmode =="percent":
            cmode = command_t.modedef.index(conmode)
        elif conmode == "amps":
            cmode = command_t.modedef.index(conmode)
        elif conmode == "voltage":
            cmode = command_t.modedef.index("volts")
        elif conmode == "ohms":
            cmode = command_t.modedef.index(conmode)
        elif conmode == "train":
            cmode = command_t.modedef.index(conmode)
        elif conmode == "count":
            cmode = command_t.modedef.index(conmode)
        elif type(conmode) == int:
            cmode = conmode
        else:
            D.debug(DEBUG_LEVELS['ERROR'], "Node", f"Error: Incorrect option")
            return    
          
        muscles = self.muscles
        if device == "all":
            for m in muscles.values():
                m.cmode = command_t.modedef[cmode]
                command = command_t(self, SM, device =  f"m{m.portNum+1}", params = [command_t.modedef.index(m.cmode)])
                self.net.command_buff.append(command)
        else:
            for m in muscles.keys():
                if str(device) == m :
                    self.muscles[m].cmode = command_t.modedef[cmode]
                    command = command_t(self, SM, device = f"m{muscles[m].portNum+1}", params = [command_t.modedef.index(muscles[m].cmode)])
                    self.net.command_buff.append(command)
                    D.debug(DEBUG_LEVELS['DEBUG'], "muscle", f"Node {self.id} added command to network buffer {self.net.idnum}")
      
    def setSetpoint(self, setpoint:float, conmode, device):   #takes muscle port and 
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id}: Setting setpoint for {device} to {setpoint}")
        #TODO: call muscle port number
        if type(device) == int:
            muscl = f"m{self.muscles[str(device)].portNum+1}"     
            cmode = conmode
            command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
            self.net.command_buff.append(command)
        elif type(device) == str:

            if device == 'all':
                for m in self.muscles:
                    muscl = f"m{m.portNum+1}"     
                    cmode = conmode
                    command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
                    self.net.command_buff.append(command)
            
            else:
                device = device.lower().split(' ',4)
                for x in device:
                    x = x.strip()
                    if 'm' in x:
                        muscl = f"m{self.muscles[x.strip('m')].portNum+1}"     
                        cmode = conmode
                        command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
                        self.net.command_buff.append(command)
                    else:
                        for y in self.muscles:
                            if int(x) == y.mosfetnum:
                                muscl = f"m{y.portNum+1}"
                                cmode = conmode
                                command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
                                self.net.command_buff.append(command)

        
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id} added command to network buffer {self.net.idnum}")
     
    def attachMuscle(self, muscle:object, portNum:int): # takes muscle object and idnumber and adds to a dictionary
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id}: Setting muscle {portNum} to {muscle}")
        '''
        
        Adds the selected muscle to the node and assigns an id number
        
        '''
        self.muscles[str(portNum)] = muscle
        muscle.masternode = self
        muscle.portNum = portNum
        mvlist = list(self.muscles.values())
        muscle.mosfetnum = mvlist.index(muscle)
        self.mosports = len(self.muscles)
    
    # TODO why is this muscle an object and the setMuscle() takes an int ??? and the muscle list is a dictionary with "1" not as an index.
    # setMuscle take the ID number of the muscle and sets the string idnumber as the dictionary key, this prevents multiple muscles having the same idnumber in a node
    def enable(self, muscle:object):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id}: Enabling muscle {muscle.portNum}")
        '''
        
        Enables the muscle selected.
        
        '''
        self.net.command_buff.append(command_t(self, SE, device = f'm{muscle.portNum+1}', params = [True]))
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id} added command to network buffer {self.net.idnum}")

    def enableAll(self):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id}: Enabling all muscles")
        '''
        
        Enables all muscles.
        
        '''
        
        for x in self.muscles.keys():
            command = command_t(self, SE, device = f'm{self.muscles[x].portNum+1}', params = [True] ) 
            self.net.command_buff.append(command)
     
    def disable(self, muscle:object):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id}: Disabling muscle {muscle.portNum}")
        '''
        
        Disables the muscle selected.
        
        '''
        self.net.command_buff.append(command_t(self, SE, device = f'm{muscle.portNum+1}', params =  [False]))
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id} added command to network buffer {self.net.idnum}")

    def disableAll(self):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id}: Disabling all muscles")
        '''
        
        Disables all muscles.
        
        '''
        for x in self.muscles.keys():
            command = command_t(self, SE, device = f'm{self.muscles[x].portNum+1}', params = [False] )
            self.net.command_buff.append(command)

    def endself(self):
        """Clean up node resources and remove from network"""
        self.cleanup()
        if self.net:
            # Let the network handle node removal
            self.net.remove_node(self.id, deactivate=False)
        del self

    
#---------------------------------------------------------------------------------------  

class Muscle:
    def __init__(self, _port:int, masternode:Node = None):
        self.portNum = _port 
        self.mosfetnum = None
        self.cmode = "percent"
        self.masternode = masternode
        self.enable_status = None
        self.train_state = None
        self.SMA_status = {'pwm_out':[],'load_amps':[],'load_voltdrop':[],'SMA_default_mode':None,'SMA_deafult_setpoint':None,'SMA_rcontrol_kp':None,'SMA_rcontrol_ki':None,'SMA_rcontrol_kd':None, 'vld_scalar':None,'vld_offset':None,'r_sns_ohms':[],'amp_gain':[],'af_mohms':[],'delta_mohms':[]}

    def cleanup(self):
        """Clean up muscle resources"""
        self.enable_status = None
        self.train_state = None
        self.SMA_status.clear()
        D.debug(DEBUG_LEVELS['DEBUG'], "Muscle", f"Muscle {self.portNum} cleaned up")

    def attach(self, masternode:Node, portNum:int=-1):
        if portNum != -1: # Makes portNum optional
            self.portNum = portNum
        masternode.attachMuscle(self, self.portNum)

    def muscleStatus(self):
        """Get formatted muscle status string"""
        status_parts = []
        for key, value in self.SMA_status.items():
            if isinstance(value, list) and value:
                # For list values, get the most recent (first) entry
                status_parts.append(f'{key}:{value[0]}')
            elif value is not None:
                # For non-list values
                status_parts.append(f'{key}:{value}')
        
        status_string = ', '.join(status_parts)
        D.debug(DEBUG_LEVELS['DEBUG'], "Muscle", f"Muscle {self.portNum}: Status = {status_string}")
        return status_string
    
    def getResistance(self):
        """Get the most recent resistance reading"""
        resistance_list = self.SMA_status.get('r_sns_ohms', [])
        if isinstance(resistance_list, list) and resistance_list:
            return resistance_list[0]  # Return most recent value
        return resistance_list  # Return the value as-is if not a list
    
    def changeMusclemos(self, mosfetnum:int):
        '''
        
        Changes the mosfet number of the given muscle.
        
        '''
        self.mosfetnum = mosfetnum 
    
    def setMode(self, conmode, out = 0):
        '''

        Sets the data mode that the muscle will recieve.

        '''
         
        if conmode =="percent":
            self.cmode = conmode
        elif conmode == "amps":
            self.cmode = conmode
        elif conmode == "voltage":
            self.cmode = "volts"
        elif conmode == "ohms":
            self.cmode = conmode
        elif conmode == "train":
            self.cmode = conmode
        elif conmode == "count":
            self.cmode = conmode
        else:
            D.debug(DEBUG_LEVELS['ERROR'], "muscle", f"Error: Incorrect option")
            return             
        
        mode = command_t.modedef.index(self.cmode) 

        if out == 0:
            muscle = self.portNum
            self.masternode.setMode(mode, muscle)
        elif out == 1:
            return mode
           
    def setSetpoint(self, conmode = None, setpoint:float = None):   #takes given setpoint and sends relevant information to node
        #TODO connode
        if conmode:
            mode = self.setMode(conmode, 1)        
        else:
            mode = command_t.modedef.index(self.cmode)        
        
        if not setpoint:
            raise KeyError("Command 'setSetpoint' requires setpoint argument.")
        self.masternode.setSetpoint(mode, self.portNum, setpoint)      
    
    def setEnable(self, bool):
        '''
        Sets the enable staus of the muscle.
        
        Parameters
        ----------
        bool : TYPE
       
        '''

        if bool:
            self.masternode.enable(self)
        else:
            self.masternode.disable(self)
         
#----------------------------------------------------------------------------------------------------


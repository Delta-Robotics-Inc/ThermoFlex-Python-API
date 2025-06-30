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
        self.node_status = {'uptime':None, 'errors':[],'volt_supply':None,'pot_values':None,'log_interval':None,'vrd_scalar':None,'vrd_offset':None,'max_current':None,'min_v_supply':None,'v_supply_raw':None}
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

    def status(self, type, device='all'):
        """Request and collect status from the device
        
        Args:
            type (str): Status type - 'compact' or 'dump'
            device (str): Device target - 'all' (default), 'node', 'portall', 'm1', 'm2'
                         'all' = DEVICE_ALL (node + all muscles)
                         'node' = DEVICE_NODE (node only)
                         'portall' = DEVICE_PORTALL (all muscles only)
                         'm1' = DEVICE_PORT1 (muscle 1 only)
                         'm2' = DEVICE_PORT2 (muscle 2 only)
        """
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Requesting {type} status from device '{device}'")
        
        if type == 'dump':
            status = command_t(self, name = 'status', params = [2], device = device)
            self.net.command_buff.append(status)
            D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Added dump status request for device '{device}' to command buffer")
            t.sleep(0.5)
            return self.status_curr
        elif type == 'compact':
            status = command_t(self, name = 'status', params = [1], device = device)
            self.net.command_buff.append(status)
            D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.id}: Added compact status request for device '{device}' to command buffer")
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
                    # Handle protocol-compliant field names
                    if key == 'errors' and 'error_code' in resp_data:
                        # Protocol uses 'error_code', we store as 'errors' list
                        self.node_status[key].insert(0, resp_data['error_code'])
                        enforce_size_limit(self.node_status[key])
                    elif key == 'volt_supply' and 'v_supply' in resp_data:
                        # Protocol uses 'v_supply', we store as 'volt_supply'
                        self.node_status[key] = resp_data['v_supply']
                    elif key == 'pot_values' and 'pot_val' in resp_data:
                        # Protocol uses 'pot_val', we store as 'pot_values'
                        self.node_status[key] = resp_data['pot_val']
                    elif key == 'log_interval' and 'log_interval_ms' in resp_data:
                        # Protocol uses 'log_interval_ms', we store as 'log_interval'
                        self.node_status[key] = resp_data['log_interval_ms']
                    elif key in resp_data:  # Direct field match
                        if type(self.node_status[key]) == list:
                            self.node_status[key].insert(0, resp_data[key])
                            enforce_size_limit(self.node_status[key])
                        else:
                            self.node_status[key] = resp_data[key]
                except KeyError:
                    continue
                    
            # Handle dump-specific fields with protocol-compliant names
            if resp_type[2] == 'dump':
                if 'can_id' in resp_data:
                    self.canid = resp_data['can_id']
                
                # Handle firmware version - supports both X.X and X.X.X formats
                major = resp_data.get('firmware_version_major')
                minor = resp_data.get('firmware_version_minor')
                if major is not None and minor is not None:
                    # New X.X.X format (patch defaults to 0 if not present)
                    patch = resp_data.get('firmware_version_patch', 0)
                    self.firmware = f"{major}.{minor}.{patch}"
                else:
                    # Legacy X.X format (backward compatibility)
                    major = resp_data.get('firmware_version')
                    minor = resp_data.get('firmware_subversion')
                    if major is not None and minor is not None:
                        self.firmware = f"{major}.{minor}"
                if 'board_version' in resp_data and 'board_subversion' in resp_data:
                    self.board_version = f"{resp_data['board_version']}.{resp_data['board_subversion']}"
                if 'muscle_cnt' in resp_data:
                    if resp_data['muscle_cnt'] != len(self.muscles):
                        D.debug(DEBUG_LEVELS['WARNING'], 'StatusCheck', 'Number of muscles initialized does not match the number of muscles attached to Node.')
        
        elif resp_type[1] == 'SMA':
            D.debug(DEBUG_LEVELS['DEBUG'], 'updateStatus', f'Dispersing Muscle{resp_type[3]} status')
            
            # Convert protobuf device enum to internal portNum
            # DEVICE_PORT1 = 3 -> portNum = 0 (muscle0)
            # DEVICE_PORT2 = 4 -> portNum = 1 (muscle1)
            protobuf_device_port = int(resp_type[3])  
            
            if protobuf_device_port == 3:  # DEVICE_PORT1
                internal_port_num = 0
            elif protobuf_device_port == 4:  # DEVICE_PORT2  
                internal_port_num = 1
            else:
                D.debug(DEBUG_LEVELS['ERROR'], 'updateStatus', f'Unknown protobuf device port: {protobuf_device_port}')
                return
                
            muscle_found = False
            
            for musc in self.muscles.values():
                # Match by internal portNum
                if hasattr(musc, 'portNum') and musc.portNum == internal_port_num:
                    muscle_found = True
                    
                    # Update muscle status with protocol-compliant field names
                    # The packet parser now sends correct protobuf field names
                    D.debug(DEBUG_LEVELS['DEBUG'], 'updateStatus', f'Found muscle for protobuf port {protobuf_device_port} -> internal portNum {internal_port_num}')
                    
                    # Direct field mapping - protocol compliant
                    for key in musc.SMA_status.keys():
                        try:
                            if key in resp_data:  # Direct field match
                                if type(musc.SMA_status[key]) == list:
                                    musc.SMA_status[key].insert(0, resp_data[key])
                                    enforce_size_limit(musc.SMA_status[key])
                                else:
                                    musc.SMA_status[key] = resp_data[key]
                        except KeyError:
                            continue
                    
                    # Update muscle metadata from response
                    if 'enabled' in resp_data:
                        musc.enable_status = resp_data['enabled']
                    if 'device_port' in resp_data:
                        # Store the protobuf device port for reference
                        if not hasattr(musc, 'device_port'):
                            musc.device_port = resp_data['device_port']
                    if 'trainState' in resp_data:
                        musc.train_state = resp_data['trainState']
                        
                    D.debug(DEBUG_LEVELS['DEBUG'], 'updateStatus', f'Updated muscle {musc.portNum} with protocol-compliant data')
                    break
                    
            if not muscle_found:
                D.debug(DEBUG_LEVELS['ERROR'], 'updateStatus(muscle)', f'No muscle found for protobuf device port {protobuf_device_port} (internal port {internal_port_num})')
                # Debug: Print available muscles
                for key, musc in self.muscles.items():
                    D.debug(DEBUG_LEVELS['ERROR'], 'updateStatus', f'Available muscle {key}: portNum={musc.portNum}, mosfetnum={musc.mosfetnum}')
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
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.id}: Setting setpoint for device {device} to {setpoint} (mode: {conmode})")
        #TODO: call muscle port number
        if type(device) == int:
            muscl = f"m{self.muscles[str(device)].portNum+1}"     
            cmode = conmode
            command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
            self.net.command_buff.append(command)
        elif type(device) == str:

            if device == 'all':
                for m in self.muscles.values():
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
                        for y in self.muscles.values():
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

    def getMuscleStatus(self, type='compact'):
        """Request status from all muscle ports only (DEVICE_PORTALL)
        
        Args:
            type (str): Status type - 'compact' or 'dump'
        """
        return self.status(type, device='portall')
    
    def getNodeOnlyStatus(self, type='compact'):
        """Request status from node only (DEVICE_NODE)
        
        Args:
            type (str): Status type - 'compact' or 'dump'  
        """
        return self.status(type, device='node')
    
    def getAllDeviceStatus(self, type='compact'):
        """Request status from all devices - node and muscles (DEVICE_ALL)
        
        Args:
            type (str): Status type - 'compact' or 'dump'
        """
        return self.status(type, device='all')

    # ============================================================================
    # Node Status Accessor Methods
    # ============================================================================
    
    def get_supply_voltage(self) -> float:
        """Get the current supply voltage reading in volts.
        
        Returns:
            float: Supply voltage in volts, or None if not available
        """
        return self.node_status.get('volt_supply')
    
    def get_supply_voltage_raw(self) -> int:
        """Get the raw ADC reading for supply voltage (before scaling).
        
        Returns:
            int: Raw ADC reading, (0-1023) or None if not available
        """
        return self.node_status.get('v_supply_raw')
    
    def get_uptime(self) -> int:
        """Get the node uptime in milliseconds.
        
        Returns:
            int: Uptime in milliseconds, or None if not available
        """
        return self.node_status.get('uptime')
    
    def get_error_code(self) -> int:
        """Get the most recent error code.
        
        Returns:
            int: Most recent error code, or None if no errors
        """
        errors = self.node_status.get('errors', [])
        return errors[0] if errors else None
    
    def get_error_history(self) -> list:
        """Get the complete error history.
        
        Returns:
            list: List of error codes (most recent first), empty list if no errors
        """
        return self.node_status.get('errors', []).copy()
    
    def get_potentiometer_value(self) -> float:
        """Get the current potentiometer reading.
        
        Returns:
            float: Potentiometer value, or None if not available
        """
        return self.node_status.get('pot_values')
    
    def get_log_interval(self) -> int:
        """Get the current logging interval in milliseconds.
        
        Returns:
            int: Log interval in milliseconds, or None if not available
        """
        return self.node_status.get('log_interval')
    
    def get_voltage_divider_scalar(self) -> float:
        """Get the voltage divider scalar value.
        
        Returns:
            float: VRD scalar value, or None if not available
        """
        return self.node_status.get('vrd_scalar')
    
    def get_voltage_divider_offset(self) -> float:
        """Get the voltage divider offset value.
        
        Returns:
            float: VRD offset value, or None if not available
        """
        return self.node_status.get('vrd_offset')
    
    def get_max_current(self) -> float:
        """Get the maximum current limit.
        
        Returns:
            float: Maximum current in amps, or None if not available
        """
        return self.node_status.get('max_current')
    
    def get_min_supply_voltage(self) -> float:
        """Get the minimum supply voltage threshold.
        
        Returns:
            float: Minimum supply voltage in volts, or None if not available
        """
        return self.node_status.get('min_v_supply')
    
    def get_firmware_version(self) -> str:
        """Get the firmware version string.
        
        Returns:
            str: Firmware version in X.X.X format (e.g., "1.2.13"), or None if not available
        """
        return self.firmware
    
    def get_board_version(self) -> str:
        """Get the board version string.
        
        Returns:
            str: Board version (e.g., "2.1"), or None if not available
        """
        return self.board_version
    
    def get_can_id(self) -> int:
        """Get the CAN bus ID.
        
        Returns:
            int: CAN ID, or None if not available
        """
        return self.canid
    
    def get_node_id_string(self) -> str:
        """Get the node ID as a formatted string.
        
        Returns:
            str: Node ID in format "1.0.17"
        """
        return ".".join(str(b) for b in self.id)
    
    def get_node_active_status(self) -> bool:
        """Check if the node is currently active (responding to heartbeats).
        
        Returns:
            bool: True if node is active, False otherwise
        """
        return self.is_active
    
    def has_errors(self) -> bool:
        """Check if the node has any recorded errors.
        
        Returns:
            bool: True if there are errors, False otherwise
        """
        errors = self.node_status.get('errors', [])
        return len(errors) > 0

#---------------------------------------------------------------------------------------  

class Muscle:
    def __init__(self, _port:int, masternode:Node = None):
        self.portNum = _port 
        self.mosfetnum = None
        self.cmode = "percent"
        self.masternode = masternode
        self.enable_status = None
        self.train_state = None
        
        # Protocol-compliant SMA_status fields based on tfnode_messages_pb2.py
        self.SMA_status = {
            # Current state fields (from SMAStatusCompact) - protocol compliant
            'device_port': None,                # Device device_port (DEVICE_PORT1/PORT2)
            'enabled': None,                    # bool enabled
            'mode': None,                       # SMAControlMode mode (current active mode)
            'setpoint': None,                   # float setpoint (current active setpoint)
            'output_pwm': [],                   # float output_pwm
            'load_amps': [],                    # float load_amps
            'load_vdrop': [],                   # float load_vdrop  
            'load_mohms': [],                   # float load_mohms
            
            # Default/configuration fields (from SMAControllerSettings - only in dump status)
            'default_mode': None,               # SMAControlMode default_mode
            'default_setpoint': None,           # float default_setpoint
            'rctrl_kp': None,                   # float rctrl_kp
            'rctrl_ki': None,                   # float rctrl_ki
            'rctrl_kd': None,                   # float rctrl_kd
            
            # Additional dump status fields (from SMAStatusDump) - protocol compliant
            'vld_scalar': None,                 # float vld_scalar
            'vld_offset': None,                 # float vld_offset
            'r_sns_ohms': [],                   # float r_sns_ohms
            'amp_gain': [],                     # float amp_gain
            'af_mohms': [],                     # float af_mohms
            'delta_mohms': [],                  # float delta_mohms
            'trainState': None,                 # TrainState trainState
        }

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
        
        if setpoint is None:
            raise KeyError("Command 'setSetpoint' requires setpoint argument.")
        # Fixed parameter order: setpoint, conmode, device (not mode, portNum, setpoint)
        self.masternode.setSetpoint(setpoint, mode, self.portNum)
    
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
         
    def status(self, type='compact'):
        """Request status for this specific muscle
        
        Args:
            type (str): Status type - 'compact' or 'dump'
        """
        if not self.masternode:
            D.debug(DEBUG_LEVELS['ERROR'], "Muscle", f"Muscle {self.portNum}: No master node attached")
            return None
            
        device = f'm{self.portNum+1}'  # Convert portNum to device format (m1, m2)
        return self.masternode.status(type, device=device)
    
    # ============================================================================
    # Muscle Status Accessor Methods
    # ============================================================================
    
    def is_enabled(self) -> bool:
        """Check if the muscle is currently enabled.
        
        Returns:
            bool: True if enabled, False if disabled, None if unknown
        """
        return self.SMA_status.get('enabled')
    
    def get_mode(self) -> int:
        """Get the current control mode.
        
        Returns:
            int: Current control mode (SMAControlMode enum), or None if not available
        """
        return self.SMA_status.get('mode')
    
    def get_setpoint(self) -> float:
        """Get the current setpoint value.
        
        Returns:
            float: Current setpoint value, or None if not available
        """
        return self.SMA_status.get('setpoint')
    
    def get_output_pwm(self) -> float:
        """Get the most recent PWM output value.
        
        Returns:
            float: Most recent PWM output value, or None if not available
        """
        output_pwm = self.SMA_status.get('output_pwm', [])
        if isinstance(output_pwm, list) and output_pwm:
            return output_pwm[0]  # Return most recent value
        return output_pwm
    
    def get_current(self) -> float:
        """Get the most recent current reading in amps.
        
        Returns:
            float: Most recent current reading in amps, or None if not available
        """
        load_amps = self.SMA_status.get('load_amps', [])
        if isinstance(load_amps, list) and load_amps:
            return load_amps[0]  # Return most recent value
        return load_amps
    
    def get_current_history(self) -> list:
        """Get the complete current reading history.
        
        Returns:
            list: List of current readings (most recent first), empty list if no data
        """
        load_amps = self.SMA_status.get('load_amps', [])
        return load_amps.copy() if isinstance(load_amps, list) else []
    
    def get_voltage_drop(self) -> float:
        """Get the most recent voltage drop reading in volts.
        
        Returns:
            float: Most recent voltage drop in volts, or None if not available
        """
        load_vdrop = self.SMA_status.get('load_vdrop', [])
        if isinstance(load_vdrop, list) and load_vdrop:
            return load_vdrop[0]  # Return most recent value
        return load_vdrop
    
    def get_resistance(self) -> float:
        """Get the most recent resistance reading in milliohms.
        
        Returns:
            float: Most recent resistance in milliohms, or None if not available
        """
        load_mohms = self.SMA_status.get('load_mohms', [])
        if isinstance(load_mohms, list) and load_mohms:
            return load_mohms[0]  # Return most recent value
        return load_mohms
    
    def get_resistance_history(self) -> list:
        """Get the complete resistance reading history.
        
        Returns:
            list: List of resistance readings in milliohms (most recent first)
        """
        load_mohms = self.SMA_status.get('load_mohms', [])
        return load_mohms.copy() if isinstance(load_mohms, list) else []
    
    def get_device_port(self) -> int:
        """Get the device port enum value.
        
        Returns:
            int: Device port enum (DEVICE_PORT1=3, DEVICE_PORT2=4), or None if not available
        """
        return self.SMA_status.get('device_port')
    
    def get_port_number(self) -> int:
        """Get the muscle port number (0-based).
        
        Returns:
            int: Port number (0 for first muscle, 1 for second muscle, etc.)
        """
        return self.portNum
    
    def get_muscle_id(self) -> str:
        """Get a formatted muscle identifier string.
        
        Returns:
            str: Muscle ID in format "Node_ID.port_number" (e.g., "1.0.17.0")
        """
        if self.masternode:
            node_id = self.masternode.get_node_id_string()
            return f"{node_id}.{self.portNum}"
        return f"unattached.{self.portNum}"
    
    # Default/Configuration Accessors (dump status only)
    
    def get_default_mode(self) -> int:
        """Get the default control mode (dump status only).
        
        Returns:
            int: Default control mode, or None if not available
        """
        return self.SMA_status.get('default_mode')
    
    def get_default_setpoint(self) -> float:
        """Get the default setpoint value (dump status only).
        
        Returns:
            float: Default setpoint value, or None if not available
        """
        return self.SMA_status.get('default_setpoint')
    
    def get_pid_kp(self) -> float:
        """Get the PID Kp (proportional) gain value (dump status only).
        
        Returns:
            float: PID Kp gain, or None if not available
        """
        return self.SMA_status.get('rctrl_kp')
    
    def get_pid_ki(self) -> float:
        """Get the PID Ki (integral) gain value (dump status only).
        
        Returns:
            float: PID Ki gain, or None if not available
        """
        return self.SMA_status.get('rctrl_ki')
    
    def get_pid_kd(self) -> float:
        """Get the PID Kd (derivative) gain value (dump status only).
        
        Returns:
            float: PID Kd gain, or None if not available
        """
        return self.SMA_status.get('rctrl_kd')
    
    def get_train_state(self) -> int:
        """Get the current training state.
        
        Returns:
            int: Training state enum value, or None if not available
        """
        return self.SMA_status.get('trainState')
    
    # Advanced diagnostic accessors (dump status only)
    
    def get_voltage_load_scalar(self) -> float:
        """Get the voltage load scalar value (dump status only).
        
        Returns:
            float: VLD scalar value, or None if not available
        """
        return self.SMA_status.get('vld_scalar')
    
    def get_voltage_load_offset(self) -> float:
        """Get the voltage load offset value (dump status only).
        
        Returns:
            float: VLD offset value, or None if not available
        """
        return self.SMA_status.get('vld_offset')
    
    def get_sense_resistance(self) -> float:
        """Get the most recent sense resistance reading (dump status only).
        
        Returns:
            float: Most recent sense resistance in ohms, or None if not available
        """
        r_sns_ohms = self.SMA_status.get('r_sns_ohms', [])
        if isinstance(r_sns_ohms, list) and r_sns_ohms:
            return r_sns_ohms[0]  # Return most recent value
        return r_sns_ohms
    
    def get_amplifier_gain(self) -> float:
        """Get the most recent amplifier gain reading (dump status only).
        
        Returns:
            float: Most recent amplifier gain, or None if not available
        """
        amp_gain = self.SMA_status.get('amp_gain', [])
        if isinstance(amp_gain, list) and amp_gain:
            return amp_gain[0]  # Return most recent value
        return amp_gain

#----------------------------------------------------------------------------------------------------


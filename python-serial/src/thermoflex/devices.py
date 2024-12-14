'''
Comments
'''
#TODO: add status parsing

import time as t
from .tools.packet import command_t
from .tools.nodeserial import send_command, send_command_str, threaded
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
    nodel = []
    def __init__(self, idnum, network=None, mosports:int = 2): #network status
        Node.nodel.append(self)
        self.index = idnum
        self.serial = None 
        self.net = network
        self.arduino = self.net.arduino
        self.logmode = 0
        self.node_id = None
        self.canid = None
        self.firmware = None
        self.board_version = None
        self.node_status = {'uptime':None, 'errors':[],'volt_supply':None,'pot_values':None,'log_interval':None,'vrd_scalar':None,'vrd_offset':None,'max_current':None,'min_v_supply':None}
        self.mosports = mosports  #mosfet ports
        self.muscles = {}
        self.logstate = {'printlog':False, 'binarylog':False, 'filelog': False}
        self.status_curr = None
        self.latest_resp = None
        self.bufflist = []
        self.lastcmnd = None

        # Make default muscles
        self.muscle0 = Muscle(0, 0, 0, 0, self)
        self.muscle1 = Muscle(1, 0, 0, 0, self)
        self.muscles = {"0":self.muscle0, "1":self.muscle1}
  
    def testMuscles(self, sendformat:int = 1):
        '''
        
        Tests the node and muscle connections. Send format takes integer; 0 for ascii, 1 for string format

        '''          
        
        self.net.openPort()
        mode = command_t.modedef('percent')
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
        
        self.closePort()
        
    def status(self,type):
        '''
        
        Requsts and collects the status from the device.
                
        '''
        if type == 'dump':
            try:
                self.net.openPort()
            finally:
                status = command_t(self, name = 'status', params = [2])
                #send_command(status,self.net)
                #send_command_str(status,self.net)
                self.net.command_buff.append(status)
                t.sleep(0.5)
                
                return self.status_curr

        elif type == 'compact':
            try:
                self.net.openPort()
            finally:
                status = command_t(self, name = 'status', params = [1])
                #send_command(status,self.net)
                #send_command_str(status,self.net)
                self.net.command_buff.append(status)
                t.sleep(0.5)

                return self.status_curr

    def getStatus(self):
        return self.status_curr

    def updateStatus(self,inc_data):

        resp_type, resp_data = inc_data
        resp_type = resp_type.split(' ')
        if resp_type[1] == 'node':
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
            D.debug(DEBUG_LEVELS['ERROR'], 'updateStatus', 'Incompatible status type.')
        status_str = str(self.node_status).replace('{','').replace('}','').replace("'",'')
        self.status_curr = f'Node{self.index}, Address:{self.node_id}, Firmware:{self.firmware}, Board version:{self.board_version}, {status_str}'

    def reset(self, device = "node"):
        '''
        Sends the reset command to the node
        '''
        try:
            self.net.openPort()
        finally:
            reset = command_t(self, name = 'reset', params = [], device = device)
            send_command(reset,self.net)
            #send_command_str(reset)
 
    def setLogmode(self, mode:int):
        '''
        Sets the log staus of the node.
        
        Parameters
        ----------
        mode 
            0:none
            1:compact
            2:dump
            3:readable dump     
    
        '''
        self.logmode = mode
        command = command_t(self, name = LOGMODE, device = "all", params = [mode])
        self.net.command_buff.append(command)

    def setMode(self, conmode, device = 'all'):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Setting mode for port {device} to {conmode}")
        '''
        
        Sets the data mode that the muscle will recieve. identify muscles by dictionary key.
        
        '''
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Setting mode for port {device} to {conmode}")

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
                command = command_t(self, SM, device =  f"m{m.idnum+1}", params = [command_t.modedef.index(m.cmode)])
                self.net.command_buff.append(command)
        else:
            for m in muscles.keys():
                if str(device) == m :
                    self.muscles[m].cmode = command_t.modedef[cmode]
                    command = command_t(self, SM, device = f"m{muscles[m].idnum+1}", params = [command_t.modedef.index(muscles[m].cmode)])
                    self.net.command_buff.append(command)
                    D.debug(DEBUG_LEVELS['DEBUG'], "muscle", f"Node {self.node_id} added command to network buffer {self.net.idnum}")
      
    def setSetpoint(self, conmode, device, setpoint:float):   #takes muscle port and 
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Setting setpoint for {device} to {setpoint}")
        #TODO: call muscle port number
        if type(device) == int:
            muscl = f"m{self.muscles[str(device)].idnum+1}"     
            cmode = conmode
            command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
            self.net.command_buff.append(command)
        elif type(device) == str:

            if device == 'all':
                for m in self.muscles:
                    muscl = f"m{m.idnum+1}"     
                    cmode = conmode
                    command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
                    self.net.command_buff.append(command)
            
            else:
                device = device.lower().split(' ',4)
                for x in device:
                    x = x.strip()
                    if 'm' in x:
                        muscl = f"m{self.muscles[x.strip('m')].idnum+1}"     
                        cmode = conmode
                        command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
                        self.net.command_buff.append(command)
                    else:
                        for y in self.muscles:
                            if int(x) == y.mosfetnum:
                                muscl = f"m{y.idnum+1}"
                                cmode = conmode
                                command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
                                self.net.command_buff.append(command)

        
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.node_id} added command to network buffer {self.net.idnum}")
     
    def setMuscle(self, idnum:int, muscle:object): # takes muscle object and idnumber and adds to a dictionary
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Setting muscle {idnum} to {muscle}")
        '''
        
        Adds the selected muscle to the node and assigns an id number
        
        '''
        self.muscles[str(idnum)] = muscle
        muscle.masternode = self
        mvlist = list(self.muscles.values())
        muscle.mosfetnum = mvlist.index(muscle)
        self.mosports = len(self.muscles)
    
    # TODO why is this muscle an object and the setMuscle() takes an int ??? and the muscle list is a dictionary with "1" not as an index.
    # setMuscle take the ID number of the muscle and sets the string idnumber as the dictionary key, this prevents multiple muscles having the same idnumber in a node
    def enable(self, muscle:object):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Enabling muscle {muscle.idnum}")
        '''
        
        Enables the muscle selected.
        
        '''
        self.net.command_buff.append(command_t(self, SE, device = f'm{muscle.idnum+1}', params = [True]))
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.node_id} added command to network buffer {self.net.idnum}")

    def enableAll(self):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Enabling all muscles")
        '''
        
        Enables all muscles.
        
        '''
        
        for x in self.muscles.keys():
            command = command_t(self, SE, device = f'm{self.muscles[x].idnum+1}', params = [True] ) 
            self.net.command_buff.append(command)
     
    def disable(self, muscle:object):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Disabling muscle {muscle.idnum}")
        '''
        
        Disables the muscle selected.
        
        '''
        self.net.command_buff.append(command_t(self, SE, device = f'm{muscle.idnum+1}', params =  [False]))
        D.debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.node_id} added command to network buffer {self.net.idnum}")

    def disableAll(self):
        D.debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Disabling all muscles")
        '''
        
        Disables all muscles.
        
        '''
        for x in self.muscles.keys():
            command = command_t(self, SE, device = f'm{self.muscles[x].idnum+1}', params = [False] )
            self.net.command_buff.append(command)
                                                             
#---------------------------------------------------------------------------------------  

class Muscle:
    def __init__(self, idnum:int, resist = None, diam = None, length = None, masternode:object = None):
        self.idnum = idnum 
        self.mosfetnum = None
        self.resistance = resist
        self.diameter = diam
        self.length = length
        self.cmode = "percent"
        self.masternode = masternode
        self.enable_status = None
        self.train_state = None
        self.SMA_status = {'pwm_out':[],'load_amps':[],'load_voltdrop':[],'SMA_default_mode':None,'SMA_deafult_setpoint':None,'SMA_rcontrol_kp':None,'SMA_rcontrol_ki':None,'SMA_rcontrol_kd':None, 'vld_scalar':None,'vld_offset':None,'r_sns_ohms':[],'amp_gain':[],'af_mohms':[],'delta_mohms':[]}

    def muscleStatus(self):
        status = ""
        for state in status:
            if type(state) == list:
                status += f'{state}:{self.SMA_status[state][0]}'
            else:
                status += f'{state}:{self.SMA_status[state]}'
        return status
    
    def getResistance(self):
        return self.SMA_status['r_sns_ohms']
    
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
            muscle = self.idnum
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
        self.masternode.setSetpoint(mode, self.idnum, setpoint)      
    
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


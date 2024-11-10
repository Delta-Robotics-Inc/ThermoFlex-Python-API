'''
Comments
'''
#TODO: rework serial reading; use read_until, read, threading,in_waiting.

import time as t
from .tools.packet import command_t
from .tools.nodeserial import send_command, send_command_str
from .controls import debug, DEBUG_LEVELS

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
#proto file definitions

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
        self.node_status = {'uptime':None, 'errors':[],'volt_supply':None,'pot_values':None,'vrd_scalar':None,'vrd_offset':None,'max_current':None,'min_v_supply':None}
        self.mosports = mosports  #mosfet ports
        self.muscles = {}
        self.logstate = {'filelog':False, 'dictlog':False, 'printlog':False, 'binarylog':False}
        self.status_curr = None
        self.latest_resp = None
        self.bufflist = []
        self.lastcmnd = None
        
        
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
        debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Setting mode for port {device} to {conmode}")
        '''
        
        Sets the data mode that the muscle will recieve. identify muscles by dictionary key.
        
        '''
        cmode = None
        if conmode =="percent":
            cmode = command_t.modedef.index(conmode)
        elif conmode == "amps":
            cmode = command_t.modedef.index(conmode)
        elif conmode == "voltage" :
            cmode = command_t.modedef.index("volts")
        elif conmode == "ohms":
            cmode = command_t.modedef.index(conmode)
        elif type(conmode) == int:
            cmode = conmode
        else:
            debug(DEBUG_LEVELS['ERROR'], "Node", f"Error: Incorrect option")
            return    
          
        muscles = self.muscles
        if device == "all":
            for m in muscles.values():
                m.cmode = cmode
                command = command_t(self, SM, device =  f"m{m.idnum+1}", params = [m.cmode])
                self.net.command_buff.append(command)
        else:
            for m in muscles.keys():
                if str(device) == m :
                    self.muscles[m].cmode = cmode
                    command = command_t(self, SM, device = f"m{muscles[m].idnum+1}", params = [muscles[m].cmode])
                    self.net.command_buff.append(command)
                    debug(DEBUG_LEVELS['DEBUG'], "muscle", f"Node {self.node_id} added command to network buffer {self.net.idnum}")
      
    def setSetpoint(self, musc:int, conmode, setpoint:float):   #takes muscle object idnumber and 
        debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Setting setpoint for {musc} to {setpoint}")

        muscl = f"m{self.muscles[str(musc)].idnum+1}"     
        cmode = conmode
        command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
        self.net.command_buff.append(command)
        debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.node_id} added command to network buffer {self.net.idnum}")
     
    def setMuscle(self, idnum:int, muscle:object): # takes muscle object and idnumber and adds to a dictionary
        debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Setting muscle {idnum} to {muscle}")
        '''
        
        Adds the selected muscle to the node and assigns an id number
        
        '''
        self.muscles[str(idnum)] = muscle
        muscle.masternode = self
        mvlist = list(self.muscles.values())
        muscle.mosfetnum = mvlist.index(muscle)
    
    def enable(self, muscle:object):
        debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Enabling muscle {muscle.idnum}")
        '''
        
        Enables the muscle selected.
        
        '''
        self.net.command_buff.append(command_t(self, SE, device = f'm{muscle.idnum+1}', params = [True]))
        debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.node_id} added command to network buffer {self.net.idnum}")

    def enableAll(self):
        debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Enabling all muscles")
        '''
        
        Enables all muscles.
        
        '''
        
        for x in self.muscles.keys():
            command = command_t(self, SE, device = f'm{self.muscles[x].idnum+1}', params = [True] ) 
            self.net.command_buff.append(command)
     
    def disable(self, muscle:object):
        debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Disabling muscle {muscle.idnum}")
        '''
        
        Disables the muscle selected.
        
        '''
        self.net.command_buff.append(command_t(self, SE, device = f'm{muscle.idnum+1}', params =  [False]))
        debug(DEBUG_LEVELS['DEBUG'], "Node", f"Node {self.node_id} added command to network buffer {self.net.idnum}")


    def disableAll(self):
        debug(DEBUG_LEVELS['INFO'], "Node", f"Node {self.node_id}: Disabling all muscles")
        '''
        
        Disables all muscles.
        
        '''
        for x in self.muscles.keys():
            command = command_t(self, SE, device = f'm{self.muscles[x].idnum+1}', params = [False] )
            self.net.command_buff.append(command)
                                                             
#---------------------------------------------------------------------------------------  

class muscle:
    def __init__(self, idnum:int, resist, diam, length, masternode:object = None):
        self.idnum = idnum 
        self.mosfetnum = None
        self.resistance = resist
        self.diameter = diam
        self.length = length
        self.cmode = command_t.modedef.index("percent")
        self.masternode = masternode
        self.SMA_status = {'enable_status':None,'control_mode':None,'pwm_out':None,'load_amps':[],'load_voltdrop':[],'SMA_default_mode':None,'SMA_deafult_setpoint':None,'SMA_rcontrol_kp':None,'SMA_rcontrol_ki':None,'SMA_rcontrol_kd':None, 'vld_scalar':None,'vld_offset':None,'r_sns_ohms':[],'amp_gain':[],'af_mohms':[],'delta_mohms':[]}

      
    def changeMusclemos(self, mosfetnum:int):
        '''
        
        Changes the mosfet number of the given muscle.
        
        '''
        self.mosfetnum = mosfetnum 
    
    def setMode(self, conmode):
        '''

        Sets the data mode that the muscle will recieve.

        '''
         
        if conmode =="percent":
            self.cmode = command_t.modedef.index(conmode)
        elif conmode == "amps":
            self.cmode = command_t.modedef.index(conmode)
        elif conmode == "voltage":
            self.cmode = command_t.modedef.index("volts")
        elif conmode == "ohms":
            self.cmode = command_t.modedef.index(conmode)
        elif conmode == "train":
            self.cmode = command_t.modedef.index(conmode)
        else:
            debug(DEBUG_LEVELS['ERROR'], "muscle", f"Error: Incorrect option")
            return             
         
        muscle = self.idnum
        self.masternode.setMode(self.cmode, muscle)
         
     
    def setSetpoint(self, setpoint:float):   #takes given setpoint and sends relevant information to node
        
                
        self.masternode.setSetpoint(self.idnum, self.cmode, float(setpoint))      
    
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


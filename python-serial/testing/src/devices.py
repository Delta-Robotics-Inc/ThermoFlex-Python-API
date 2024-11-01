'''
Comments
'''
#TODO: rework serial reading; use read_until, read, threading,in_waiting.
import serial as s
import time as t
from .tools import tfnode_messages_pb2 as tfproto
import struct as st
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

class node:
    nodel = []
    def __init__(self, idnum, network=None, mosports:int = 2): #network status
        node.nodel.append(self)
        self.idnum = idnum
        self.serial = None 
        self.net = network
        self.addr = None #TODO add in recieve func
        self.arduino = self.net.arduino
        self.sessid = None
        self.logmode = 0
        self.nodedict = {"A":[],"B":[],"C":[],"D":[]}
        self.m1dict = {"A":[],"B":[],"C":[],"D":[],"E":[],"F":[],"G":[],"H":[],"I":[],"J":[],"K":[],"L":[]}
        self.m2dict = {"A":[],"B":[],"C":[],"D":[],"E":[],"F":[],"G":[],"H":[],"I":[],"J":[],"K":[],"L":[]}
        self.mosports = mosports  # TODO rename this to be more verbose.  Is it number of ports?
        # TODO use this same philisophy for all variable and method names
        self.muscles = {}
        self.command_buff = []
        self.logstate = {'filelog':False, 'dictlog':False, 'printlog':False, 'binarylog':False}
        self.buffer = None
        self.bufflist = []
        self.lastcmnd = []
        
        
    def testMuscles(self, sendformat:int = 1):
        '''
        
        Tests the node and muscle connections. Send format takes integer; 0 for ascii, 1 for string format

        '''       
        
        
        self.net.openPort()
        mode = command_t.modedef[PERCENT]
        if sendformat == 1:
            send_command_str(command_t(self,"set-setpoint", [mode ,0.5], device = "m1")) # make own test command
            send_command_str(command_t(self,"set-setpoint", [mode ,0.5], device = "m2"))        
            #send_command_str(command_t(self, "log-mode", [1],device = "all"))
            #self.logmode = 1
          
            send_command_str(command_t(self, "set-enable", [True], device = "m1"))
            t.sleep(3.0)
           
            
            send_command_str(command_t(self, "set-enable", [False], device = "m1"))
            t.sleep(3.0)
           
           
            send_command_str(command_t(self, "set-enable", [True], device = "m2"))
            t.sleep(3.0)
          
            
            send_command_str(command_t(self, "set-enable", [False], device = "m2"))
            t.sleep(3.0)
          
            #send_command_str(command_t(self, "log-mode", [0],device = "all"))
            #self.logmode = 0
            print("Test complete")
        
        elif sendformat == 0:
            
            send_command(command_t(self,"set-setpoint", [mode ,0.5], device = "m1")) # make own test command
            send_command(command_t(self,"set-setpoint", [mode ,0.5], device = "m2"))        
            #send_command(command_t(self, "log-mode", [1],device = "all"))
            #self.logmode = 1
          
            send_command(command_t(self,"set-enable", [True], device = "m1"))
            t.sleep(3.0)
           
            
            send_command(command_t(self, "set-enable", [False], device = "m1"))
            t.sleep(3.0)
           
           
            send_command(command_t(self, "set-enable", [True], device = "m2"))
            t.sleep(3.0)
          
            
            send_command(command_t(self, "set-enable", [False], device = "m2"))
            t.sleep(3.0)
          
            #send_command(command_t(self, "log-mode", [0],device = "all"))
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
                send_command(status,self.net.arduino)
                #send_command_str(status,self.net.arduino)
                buffer = receive(self.net)
                #print(buffer)

                # Only return the first status message and return None if there are no messages
                if(len(buffer) > 1):
                    return tfproto.NodeCommand.FromString(buffer[1])
                else:
                    return None

        elif type == 'compact':
            try:
                self.net.openPort()
            
            finally:
                status = command_t(self, name = 'status', params = [1])
                send_command(status,self.net.arduino)
                #send_command_str(status,self.net.arduino)
                buffer = receive(self.net)

                # Only return the first status message and return None if there are no messages
                if len(buffer) > 1:
                    return tfproto.NodeCommand.FromString(buffer[1])
                else:
                    return None

        
    def reset(self, device = "node"):
        '''
        Sends the reset command to the node
        '''
        try:
            self.net.openPort()
        finally:
            reset = command_t(self, name = 'reset', params = [], device = device)
            send_command(reset,self.net.arduino)
            #send_command_str(reset)
 
    def setLogmode(self, mode:int):
        '''
        Sets the log staus of the node.
        
        Parameters
        ----------
        bool : TYPE
       
    
        '''
        self.logmode = mode
        command = command_t(self, name = LOGMODE, device = "all", params = [mode])
        self.command_buff.append(command)
        
    def setMode(self, conmode, device = 'all'):
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
            print("Error: Incorrect option" )
            return    
        
          
        muscles = self.muscles
        if device == "all":
            for m in muscles.values():
                m.cmode = cmode
                command = command_t(self, SM, device =  f"m{m.idnum+1}", params = [m.cmode])
                self.command_buff.append(command)
        else:
            for m in muscles.keys():
                if str(device) == m :
                    self.muscles[m].cmode = cmode
                    command = command_t(self, SM, device = f"m{muscles[m].idnum+1}", params = [muscles[m].cmode])
                    self.command_buff.append(command)

                
                
    def setSetpoint(self, musc:int, conmode, setpoint:float):   #takes muscle object idnumber and 
        
        muscl = f"m{self.muscles[str(musc)].idnum+1}"     
        cmode = conmode
        command = command_t(self, name = SS, device = muscl, params = [cmode, setpoint])
        self.command_buff.append(command)      
     
    def setMuscle(self, idnum:int, muscle:object): # takes muscle object and idnumber and adds to a dictionary
        '''
        
        Adds the selected muscle to the node and assigns an id number
        
        '''
        self.muscles[str(idnum)] = muscle
        muscle.masternode = self
        mvlist = list(self.muscles.values())
        muscle.mosfetnum = mvlist.index(muscle)
    
    def enable(self, muscle:object):
        '''
        
        Enables the muscle selected.
        
        '''
        self.command_buff.append(command_t(self, SE, device = f'm{muscle.idnum+1}', params = [True]))
 
    def enableAll(self):
        '''
        
        Enables all muscles.
        
        '''
        
        for x in self.muscles.keys():
            command = command_t(self, SE, device = f'm{self.muscles[x].idnum+1}', params = [True] ) 
            self.command_buff.append(command)
     
    def disable(self, muscle:object):
        '''
        
        Disables the muscle selected.
        
        '''
        self.command_buff.append(command_t(self, SE, device = f'm{muscle.idnum+1}', params =  [False]))
    
    
    def disableAll(self):
        '''
        
        Disables all muscles.
        
        '''
        for x in self.muscles.keys():
            command = command_t(self, SE, device = f'm{self.muscles[x].idnum+1}', params = [False] )
            self.command_buff.append(command)
    
    def update(self):
        '''
        
        Updates the status of the node. Send format is by default 0-ascii or 1-string format.
        
        '''
        #move update to nodenet; update net consistantly and send data to nodes, new node-level update changes values in node
        self.net.openPort()
        try:
            self.buffer = self.net.receive_packet(self) #have nodenet send and receieve packet
            
            
            if len(self.bufflist) >= 50:
                self.bufflist.pop(0)
                self.bufflist.append(self.buffer)
            else:
                self.bufflist.append(self.buffer)
            
        finally:
            for x in self.command_buff: #TODO: replace these with nodenetwork connections? format for single node and nodenetwork
                                         
                self.net.send_packet(x)
                self.lastcmnd.append(x)                                                       
                self.command_buff.remove(x)                       
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
            print("Error: Incorrect option" )
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

        if True:
            self.masternode.enable(self)
        elif False:
            self.masternode.disable(self)
         
#----------------------------------------------------------------------------------------------------


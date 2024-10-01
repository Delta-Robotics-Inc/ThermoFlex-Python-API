import serial as s
import time as t

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
COMADDR = 0x11111111111
        
def send_command_str(node:object, command): #construct string then send
    '''
    
    Send the command x as a string; Takes command_t object as arguments.
    
    '''
    command_str = None
    port = node.arduino
    command_str = f"{COMADDR} {node.addr} {node.idnum} {command.name} {command.device}"
    if command.code == 0xFF or command.code == 0x04:
        command_str = command_str
        
    elif command.code == 0xFE:
        pass
    else:    
        
        for p in command.params:
            command_str = command_str + str(p).lower() # Current string implementation
             
    port.write(f"{command_str} \n".encode('utf-8'))       
    
    t.sleep(0.05)

def send_command(node:object, command):
    '''
    
    Sends commands recieved by command_t. Takes command_t object as arguments.
    
    '''
    
    port = node.arduino
    command_final = None
    command_params = []
    command_list =[COMADDR, node.addr, node.idnum, command.code, command.devcode]
    
    if command.code == 0xFF or command.code == 0x04:
                
        command_final = bytearray(command_list)
    else:    
                
        for p in command.params:
            command_params.append(p) # Current string implementation
        
        command_final = bytearray(command_list + command_params)
    port.write(command_final)
    t.sleep(0.05)      

#TODO recieve command function

#---------------------------------------------------------------------------------------
class command_t:
    
    '''
    
    Class dedicated to holding and sending the command codes.
    
    '''
    
    commanddefs = {"set-enable": [0x01, [bool]], #state
			       "set-mode": [0x02, [int]], #mode
			       "set-setpoint": [0x03, [int, float]], #mode, value
			       "status": [0x04, []],
			       "log-mode": [0x06, [int]], #log mode(subject to change)
			       "reset": [0xFF, []]
			       } 

    devicedef = {"all": 0x07, "node": 0x00, "m1": 0x01, "m2": 0x02}
	
    modedef = {"percent": 0, "amps": 1, "volts": 2,"degree": 3,"ohms": 4, "train" : 5, "manual": 6}
          
        
    def getName(code:hex):
       for x in command_t.commanddefs:
           if code == command_t.commanddefs[x][0]:
               return x

    def isValid(self, command, params:list):
       ''' 
           
       Check if name, code, and params match one of the definitions.
           
       '''
       z = 0 
       for x in params:
           if type(x) == self.commanddefs[command][1][z]:
               z+=1
               continue
           else:
               return False
       return True
        

    def __init__(self, name:str, params:list, device = 'all' ):
    	
        self.params = params 
        self.device = device
        try:
            self.devcode = command_t.devicedef[self.device]
        except:
            raise KeyError("Incorrect device")
        self.name = name
        try:
            self.code = command_t.commanddefs[name]
        except:
            self.code = 0x00  # Invalid code reserved for 0
            raise KeyError("Invalid command name")     
                       
        if self.isValid(command = self.name, params = self.params) is True:
            pass
        elif self.isValid(command = self.name, params = self.params) is False:
            raise ValueError("Incorrect arguments for this command") 
           
#---------------------------------------------------------------------------------------

class node:
    
    def __init__(self, idnum, port0, serial, mosports:int = 2): #network status
        self.idnum = idnum
        self.serial = serial 
        self.port0 = port0
        self.address = None #TODO add in recieve func
        self.arduino = None
        self.sessid = None
        self.logmode = 0
        self.nodedict = {"A":[],"B":[],"C":[],"D":[]}
        self.m1dict = {"A":[],"B":[],"C":[],"D":[],"E":[],"F":[],"G":[],"H":[],"I":[],"J":[],"K":[],"L":[]}
        self.m2dict = {"A":[],"B":[],"C":[],"D":[],"E":[],"F":[],"G":[],"H":[],"I":[],"J":[],"K":[],"L":[]}
        self.mosports = mosports
        self.muscles = {}
        self.command_buff = []
        self.logstate = {'filelog':False, 'dictlog':False, 'printlog':False, 'binarylog':False}
        self.buffer = None
        self.bufflist = []
        
        
    
    def openPort(self): 
        '''
        
        Opens a new port with given COM port. Returns serial port.
        
        '''
        
        try:
            if self.arduino.is_open == True:
                pass
            elif self.arduino.is_open == False:
                self.arduino.open()
               
        except AttributeError:
            try:
                self.arduino = s.Serial(port = self.port0 , baudrate=115200, timeout=1)
                
            except s.SerialException:
                print('Serial not opened, check port status')        
            
        
    def closePort(self):
        '''
        
        Closes the port of the given COM port.
        
        '''
        
        
        try:
            self.arduino.close()

        except s.SerialException:
           print('Serial not closed')
           
    def testMuscles(self, sendformat:int = 1):
        '''
        
        Tests the node and muscle connections. Send format takes integer; 0 for ascii, 1 for string format

        '''       
        
        
        self.openPort()
        mode = command_t.modedef[PERCENT]
        if sendformat == 1:
            send_command_str(self, command_t("set-setpoint", [mode ,0.5], device = "m1")) # make own test command
            send_command_str(self, command_t("set-setpoint", [mode ,0.5], device = "m2"))        
            #send_command_str(self, command_t("log-mode", [1],device = "all"))
            #self.logmode = 1
          
            send_command_str(self, command_t("set-enable", [True], device = "m1"))
            t.sleep(3.0)
           
            
            send_command_str(self, command_t("set-enable", [False], device = "m1"))
            t.sleep(3.0)
           
           
            send_command_str(self, command_t("set-enable", [True], device = "m2"))
            t.sleep(3.0)
          
            
            send_command_str(self, command_t("set-enable", [False], device = "m2"))
            t.sleep(3.0)
          
            #send_command_str(self, command_t("log-mode", [0],device = "all"))
            #self.logmode = 0
            print("Test complete")
        
        elif sendformat == 0:
            
            send_command(self, command_t("set-setpoint", [mode ,0.5], device = "m1")) # make own test command
            send_command(self, command_t("set-setpoint", [mode ,0.5], device = "m2"))        
            #send_command(self, command_t("log-mode", [1],device = "all"))
            #self.logmode = 1
          
            send_command(self, command_t("set-enable", [True], device = "m1"))
            t.sleep(3.0)
           
            
            send_command(self, command_t("set-enable", [False], device = "m1"))
            t.sleep(3.0)
           
           
            send_command(self, command_t("set-enable", [True], device = "m2"))
            t.sleep(3.0)
          
            
            send_command(self, command_t("set-enable", [False], device = "m2"))
            t.sleep(3.0)
          
            #send_command(self, command_t("log-mode", [0],device = "all"))
            #self.logmode = 0
            print("Test complete")
        
        self.closePort()
        
        
    def status(self):
        '''
        
        Requsts and collects the status from the device.
                
        '''
        self.arduino.open()
        
        status = command_t(name = 'status', params = [])
        send_command(self, status)
        #send_command_str(self, status)
        
        for x in range(0,37): #30 lines for status check
            buffer = self.arduino.readline().decode("utf-8").strip()
            
            print(str(buffer))
        
        self.arduino.close()
        
    def reset(self):
        '''
        Sends the reset command to the node
        '''
        self.arduino.open()
        
        reset = command_t(name = 'reset', params = [])
        send_command(self, reset)
        #send_command_str(self, reset)
        for x in range(0,10): #30 lines for status check
            buffer = self.arduino.readline().decode("utf-8").strip()
            
            print(str(buffer))
        
        self.arduino.close()
    
    def setLogmode(self, mode:int):
        '''
        Sets the log staus of the node.
        
        Parameters
        ----------
        bool : TYPE
       
    
        '''
        self.logmode = mode
        command = command_t(name = LOGMODE, device = "all", params = [mode])
        self.command_buff.append(command)
        
    def setMode(self, conmode, device = 'all'):
        '''
        
        Sets the data mode that the muscle will recieve. identify muscles by dictionary key.
        
        '''
        cmode = None
        if conmode =="percent" or command_t.modedef[PERCENT]:
            cmode = command_t.modedef[PERCENT]
        elif conmode == "amp" or command_t.modedef[AMP]:
            cmode = command_t.modedef[AMP]
        elif conmode == "voltage" or command_t.modedef[VOLT]:
            cmode = command_t.modedef[VOLT]
        elif conmode == "degree" or command_t.modedef[DEG]:
            cmode = command_t.modedef[DEG]
        else:
            print("Error: Incorrect option" )
            return    
        
          
        muscles = self.muscles
        if device == "all":
            for m in muscles.values():
                command = command_t(SM, device =  f"m{m.idnum+1}", params = [m.cmode])
                m.cmode = cmode
                self.command_buff.append(command)
        else:
            for m in muscles.keys():
                if str(device) == m :
                    command = command_t(SM, device = f"m{muscles[m].idnum+1}", params = [muscles[m].cmode])
                    self.muscles[m].cmode = cmode
                    self.command_buff.append(command)

                
                
    def setSetpoint(self, musc:int, cmode, setpoint:float):   #takes muscle object idnumber and 
        
        muscl = f"m{self.muscles[str(musc)].idnum+1}"     
        
        command = command_t(name = SS, device = muscl, params = [cmode, setpoint])
        
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
        self.command_buff.append(command_t(SE, device = f'm{muscle.idnum+1}', params = [True]))
 
    def enableAll(self):
        '''
        
        Enables all muscles.
        
        '''
        
        for x in self.muscles.keys():
            command = command_t(SE, device = f'm{self.muscles[x].idnum+1}', params = [True] ) 
            self.command_buff.append(command)
     
    def disable(self, muscle:object):
        '''
        
        Disables the muscle selected.
        
        '''
        self.command_buff.append(command_t(SE, device = f'm{muscle.idnum+1}', params =  [False]))
    
    
    def disableAll(self):
        '''
        
        Disables all muscles.
        
        '''
        for x in self.muscles.keys():
            command = command_t(SE, device = f'm{self.muscles[x].idnum+1}', params = [False] )
            self.command_buff.append(command)
    
    def update(self, sendformat:int = 0):
        '''
        
        Updates the status of the node. Send format is by default 0-ascii or 1-string format.
        
        '''
        self.openPort()
        try:
            self.buffer = self.arduino.readline()
            
            if len(self.bufflist) >= 50:
                self.bufflist.pop(0)
                self.bufflist.append(self.buffer)
            else:
                self.bufflist.append(self.buffer)
            
            
        finally:
            for x in self.command_buff: #TODO: replace these with nodenetwork connections? format for single node and nodenetwork
                             
                if sendformat == 0:
               
                    send_command(self,x)
                    self.command_buff.remove(x)
            
                elif sendformat == 1:        
                
                    send_command_str(self,x)
                    self.command_buff.remove(x)
                
                else:
                    raise ValueError("Incorrect send format")
                                       
#---------------------------------------------------------------------------------------  

class muscle:
    def __init__(self, idnum:int, resist, diam, length, masternode:object = None):
         self.idnum = idnum 
         self.mosfetnum = None
         self.resistance = resist
         self.diameter = diam
         self.length = length
         self.cmode = command_t.modedef["percent"]
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
             self.cmode = command_t.modedef["percent"]
         elif conmode == "amp":
             self.cmode = command_t.modedef["amps"]
         elif conmode == "voltage":
             self.cmode = command_t.modedef["volts"]
         elif conmode == "degree":
             self.cmode = command_t.modedef["degree"]
         else:
             print("Error: Incorrect option" )
             return             
         
         muscle = self.idnum
         self.masternode.setMode(self.cmode, muscle)
         
     
    def setSetpoint(self, setpoint:float):   #takes given setpoint and sends relevant information to node
        
                
        self.masternode.setSetpoint(self.idnum, self.cmode, setpoint)      
    
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


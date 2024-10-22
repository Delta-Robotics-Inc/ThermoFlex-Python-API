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

STARTBYTE = 0x7E
PROTOVER = 0x01
SENDID = [0x01,0x02,0x03]
IDTYPE = 0x00
CHECKSUM = 0xFF
PROTOSIZE = 1
IDTYPESIZE = 1
IDSIZE = 3
CHECKSUM = 1

def packet_size(data:str):
    '''
    Takes data string, returns 2 element tuple of 4 digit byte data length in integer
    EX.[(01,75)]

    '''
    statics = PROTOSIZE + IDSIZE + IDSIZE + IDTYPESIZE + IDTYPESIZE + CHECKSUM
    datasize = len(data)
    length = statics + datasize
    length = f'{length}'
    while len(length)<4:
        length = '0'+length
    length = (int(length[:2]),int(length[2:]))

    return length

def checksum_cal(dest_id, data):
    # Calculate checksum
    checksum = 0
    checksum ^= PROTOVER
    checksum ^= IDTYPE
    checksum ^= IDTYPE
    for byte in SENDID:
        checksum ^= byte
    for byte in dest_id:
        checksum ^= byte
    for byte in data:
        checksum ^= byte
    return checksum

def send_command_str(command, port): #TODO: construct packet in commmand, remove send_command options
    '''
    
    Prints the command to a terminal. Used for test purposes.
    
    '''
     
    command_final = b''
    for c in command.packet:
        if type(c) == str:
            command_final += bytes(c,'ascii')
        elif type(c) == int:
            command_final += st.pack('!B', c)
    
    print(port)
    print(command.packet)
    print(command_final)
    
    t.sleep(0.05)

def send_command(command, port):
    '''
    
    Sends commands recieved by command_t. Takes command_t object as arguments.
    
    '''
    command_final = b''
    for c in command.packet:
        if type(c) == str:
            command_final += bytes(c,'ascii')
        elif type(c) == int:
            command_final += st.pack('!B', c)
    
    port.write(command_final)
    t.sleep(0.05)      


def receive(network:object):
    '''
    id address from network
    incomoing logging and changes

    '''
    start_time = t.time()
    timeout = 1  # seconds
    port = network.arduino
    i_d = b''
    while True:
        if port.in_waiting > 0:
            i_d += port.read(port.in_waiting)
            # Decode and print received data as characters
            for b in i_d: 
                if 126 == b:                    
                    try:
                        z = i_d.index(b)
                        l = i_d[z+1:z+3]
                        n = ''
                        for y in l:
                            n += str(y)
                        if int(n)+3 > port.in_waiting:
                            break
                    
                    finally:                                               
                        n = int(n)-10
                        try:
                            msg = (i_d[z+6:z+9],i_d[z+13:z+13+n].decode('ascii'))
                        except UnicodeDecodeError:
                                print("[Error decoding data]")
        elif t.time() - start_time > timeout:
            # No more data, exit loop after timeout
            break
        else:
            # No data, wait a bit before checking again
            t.sleep(0.1)

        try:
            if len(msg)>0:
                break
        except UnboundLocalError:
            pass
                
    #find packet
    return msg
#TODO: id address pull from network
#---------------------------------------------------------------------------------------
# [Start Byte][Packet Length][Protocol Version][Sender ID Type][Destination ID Type][Sender ID][Destination ID][Data][Checksum]
class command_t:
    
    '''
    
    Class dedicated to holding and sending the command codes.
    
    '''
    
    commanddefs = {"set-enable": [0x01, [bool]], #state
			       "set-mode": [0x02, [int]], #mode
			       "set-setpoint": [0x03, [int, float]], #mode, value
			       "status": [0x04, [int]], #Update to match node firmware  
                   "log-mode": [0x05, [int]], #log mode(subject to change)
			       "configure": [0x06,[int,int]],
                   "silence":[0x07,[bool]],
                   "reset": [0xFF, []]
			       } 
    devicedef = ("all", "node","portall", "m1", "m2")
	
    modedef = ("percent" , "amps", "volts", "ohms", "train")
           
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
    

    def get_device_code(self) -> tfproto.Device:
        """
          Returns the device code based on the device code index.
        """

        if self.devcode == 0:
            device_code = tfproto.Device.DEVICE_ALL
        elif self.devcode == 1:
            device_code = tfproto.Device.DEVICE_NODE
        elif self.devcode == 2:
            device_code = tfproto.Device.DEVICE_PORTALL
        elif self.devcode == 3:
            device_code = tfproto.Device.DEVICE_PORT1
        elif self.devcode == 4:
            device_code = tfproto.Device.DEVICE_PORT2

        return device_code           
        

    def set_mode(self) -> tfproto.SMAControlMode:
        
        if self.params[0] =="percent":
            mode = tfproto.SMAControlMode.MODE_PERCENT
        elif self.params[0] == "amp":
            mode = tfproto.SMAControlMode.MODE_AMPS
        elif self.params[0] == "voltage" :
            mode = tfproto.SMAControlMode.MODE_VOLTS
        elif self.params[0] == "ohms":
            mode = tfproto.SMAControlMode.MODE_OHMS
        elif self.params[0] == "train":
            mode = tfproto.SMAControlMode.MODE_TRAIN
           
        return mode
    
    def statusenum(self,param) -> tfproto.DeviceStatusMode:
        x = None
        if param == 0:
            x = tfproto.DeviceStatusMode.STATUS_NONE
        if param == 1:
            x = tfproto.DeviceStatusMode.STATUS_COMPACT
        if param == 2:
            x = tfproto.DeviceStatusMode.STATUS_DUMP
        if param == 3:
            x = tfproto.DeviceStatusMode.STATUS_DUMP_READABLE
        return x
    
    def sConstruct(self):
        '''
        Constructs the .proto command from command_t object
        '''
        node_cmd = tfproto.NodeCommand()
        if self.code == 0x01:
            if self.params[0] == True:
                node_cmd.enable.device = self.get_device_code()
            elif self.params[0] == False:
                node_cmd.disable.device = self.get_device_code()
         # ask Mark about .proto format- class structure
        elif self.code == 0x02:
            node_cmd.set_mode.device = self.get_device_code()
            node_cmd.set_mode.mode = self.set_mode()
        elif self.code == 0x03:
            node_cmd.set_setpoint.device = self.get_device_code()            
            node_cmd.set_setpoint.mode = self.set_mode()
            node_cmd.set_setpoint.setpoint = self.params[1]
        elif self.code == 0x04:
            node_cmd.status.device = self.get_device_code()
            node_cmd.status.mode = self.statusenum(self.params[0])
        elif self.code == 0x05:
            node_cmd.status.device = self.get_device_code()
            node_cmd.status.mode = 1
        elif self.code == 0x06:
            node_cmd.configure_settings.device = self.get_device_code()
            node_cmd.configure_settings.can_id = self.params[0]
        elif self.code == 0x07:
            node_cmd.silence_node.silence = self.params[0]
        elif self.code == 0xFF:
            node_cmd.reset.device = self.get_device_code()
        
        return node_cmd.SerializeToString()


    def packet_construction(self):
        
        
        packet = [PROTOVER,IDTYPE,IDTYPE]
        plength = packet_size(self.construct)
        packet.insert(0,plength[1])
        packet.insert(0,plength[0])
        packet.insert(0,STARTBYTE)
        packet.extend(SENDID)
        packet.extend(self.destnode.addr)
        packet.extend(self.construct)
        packet.append(checksum_cal(self.destnode.addr,self.construct))
        p = []
        
        #construct packet in bytes
        for x in packet:
            if type(x) == str:
                p.append(x)
            elif type(x) == int:
                p.append(x)
        
        return p
    
    def __init__(self, node:object, name:str, params:list, device = 'node' ):
    	#valid command checking
        self.params = params 
        self.device = device
        try:
            self.devcode = command_t.devicedef.index(self.device)
        except:
            raise KeyError("Incorrect device")
        self.name = name
        try:
            self.code = command_t.commanddefs[name][0]
        except:
            self.code = 0x00  # Invalid code reserved for 0
            raise KeyError("Invalid command name")     
                       
        if self.isValid(command = self.name, params = self.params) is True:
            pass
        elif self.isValid(command = self.name, params = self.params) is False:
            raise ValueError("Incorrect arguments for this command") 
        #packet construction
        self.destnode = node
        self.construct = self.sConstruct()
        self.length = packet_size(self.construct)
        self.type = IDTYPE
        self.packet = self.packet_construction()
         
#---------------------------------------------------------------------------------------

class nodenet:
    netlist = []
    def __init__(self, idnum, port):
        nodenet.netlist.append(self)
        self.idnum = idnum
        self.port = port
        self.arduino = None
        self.node0 = node(0, self)
        self.node0.addr = [0x01,0x02,0x03]
        self.nodenet = [] # list of connected nodes
        self.nodenet.append(self.node0)
        self.openPort()
        self.closePort()
        self.addNode()
        
    def addNode(self): # change later for incorporating nodes
        node0 = node(len(node.nodel)+1,self)
        node0.addr = [0x04,0x05,0x06]
        self.nodenet.append(node0)
    
    def getDevice(self,addr):
        
        for x in self.nodenet:
            if addr == x.addr:
                return x
            else:
                pass
    
        print('Node not found. Check your node address')


    def nodeonNet(self): #periodically sends network
        command_t(self.node0, name = "status", params = [1])
        send_command() #send network and recieve unknown response length
    
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
                self.arduino = s.Serial(port = self.port , baudrate=115200, timeout=1)
                
            except s.SerialException:
                print('Serial not opened, check port status')
        finally:
            return self.arduino
               
    def closePort(self):
        '''
        
        Closes the port of the given COM port.
        
        '''
        
        
        try:
            self.arduino.close()
    
        except s.SerialException:
           print('Serial not closed')
           

    
    def receive_packet(self,node = None):
        packets = []
        for x in range(0, len(self.nodenet)):
            packets.append(receive(self))
        
        #for msg in packets:
           # for node in self.nodenet:
                #if node.addr == packet_split(msg[]):
        
        pass
    
    def send_packet(self,cmd):
        send_command(cmd, self.arduino)
        
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
                return buffer[1]

        elif type == 'compact':
            try:
                self.net.openPort()
            
            finally:
                status = command_t(self, name = 'status', params = [1])
                #send_command(status,self.net.arduino)
                send_command_str(status,self.net.arduino)
                buffer = receive(self.net)
                return buffer[1]

        
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
            cmode = command_t.modedef.index(0)
        elif conmode == "amp":
            cmode = command_t.modedef.index(1)
        elif conmode == "voltage" :
            cmode = command_t.modedef.index(2)
        elif conmode == "ohms":
            cmode = command_t.modedef.index(3)
        elif type(conmode) == int:
            cmode = command_t.modedef[conmode]
        else:
            print("Error: Incorrect option" )
            return    
        
          
        muscles = self.muscles
        if device == "all":
            for m in muscles.values():
                command = command_t(self, SM, device =  f"m{m.idnum+1}", params = [m.cmode])
                m.cmode = cmode
                self.command_buff.append(command)
        else:
            for m in muscles.keys():
                if str(device) == m :
                    command = command_t(self, SM, device = f"m{muscles[m].idnum+1}", params = [muscles[m].cmode])
                    self.muscles[m].cmode = cmode
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


from .tools.nodeserial import *
from .tools.packet import command_t
from .devs import node, muscle
#TODO: id address pull from network

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
from .tools.nodeserial import serialport, send_command
from .tools.packet import command_t, deconstructor
from .devices import node, muscle
from .sessions import session
import serial as s
#TODO: id address pull from network
def sess(net):#create session one does not exist
    if session.sescount>0:
        return sessionl[0]
    else:
        return session(net)
class nodenet:
    
    netlist = []
    def __init__(self, idnum, port):
        nodenet.netlist.append(self)
        self.idnum = idnum
        self.port = port
        self.arduino = None
        self.node0 = node(0, self)
        self.node0.addr = [0x04,0x05,0x06]
        self.nodenet = [] # list of connected nodes
        self.nodenet.append(self.node0)
        self.command_buff = []
        self.sess = sess(self)
        self.openPort()
        serialport(self)
        
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
            #print(self.port,self.arduino)
            return self.arduino
               
    def closePort(self):
        '''
        
        Closes the port of the given COM port.
        
        '''
        
        
        try:
            self.arduino.close()
    
        except s.SerialException:
           print('Serial not closed')
           
    def disperse(self,rec_cmd):
        for node in self.nodenet:
            if node.addr == rec_cmd[0]:
                node.lastcmd = deconstructor(rec_cmd[1])
                #self.sess.logging(rec_cmd[1],1)
                break
    

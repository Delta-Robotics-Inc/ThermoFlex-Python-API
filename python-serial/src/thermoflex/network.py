from .tools.nodeserial import serialport, send_command
from .tools.packet import command_t, deconstructor
from .devices import node, muscle
from .sessions import session
import serial as s
import time as t
#TODO: id address pull from network
def sess(net):#create session if one does not exist
    if session.sescount>0:
        return session.sessionl[0]
    else:
        return session(net)
class nodenet:
    
    netlist = []
    def __init__(self, idnum, port):
        nodenet.netlist.append(self)
        self.idnum = idnum
        self.port = port
        self.arduino = None
        self.broadcast_node = node(0,self)
        self.node0 = node(1, self)
        self.broadcast_node.node_id = [0xFF,0xFF,0xFF]
        self.node0.node_id = [0x00,0x00,0x01]
        self.node_list = [] # list of connected nodes
        self.node_list.extend([self.broadcast_node,self.node0])
        self.command_buff = []
        self.sess = sess(self)
        self.openPort()
        serialport(self)
        
    def refreshDevices(self):
        '''
        Refreshes the network devices by sending a broadcast status command to the network.
        All devices on the network will respond with their status.
        '''
        #self.node_list = [] # Clear the list of connected nodes... should this be done?
        self.broadcast_node.status('compact') #broadcasts status to all devices
        t.sleep(0.5) # Await for responses
        # If blocking, then we know that the device list is updated when the function returns.
    
    def addNode(self,addr):
        node = node(len(node.nodel)+1,self)
        node.address = addr
        self.node_list.append(node)
    
    def removeNode(self,addr):
        for node in self.node_list:
            if node.address == addr:
                self.node_list.remove(node)

    def getDevice(self,addr):
        
        for x in self.node_list:
            if addr == x.address:
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
        response = deconstructor(rec_cmd[1])
        for node in self.node_list:
            if node.address == rec_cmd[0]:
                if 'status' in  response:
                    node.status_curr = response
                else:
                    node.latest_resp = response
                #self.sess.logging(rec_cmd[1],1)
                return
        try:
            self.addNode(rec_cmd[0])
        except:
            pass
    

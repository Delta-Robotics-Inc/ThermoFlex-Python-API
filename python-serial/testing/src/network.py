from .tools.nodeserial import serialport, send_command
from .tools.packet import command_t, deconstructor
from .devices import node, muscle
from .sessions import session
#TODO: id address pull from network
def sess():#create session one does not exist
    return 5
class nodenet:
    
    netlist = []
    def __init__(self, idnum, port):
        nodenet.netlist.append(self)
        self.idnum = idnum
        self.port = port
        self.arduino = None
        self.node0 = node(0, self)
        self.node0.addr = [0x01,0x02,0x03]
        self.node_list = [] # list of connected nodes
        self.node_list.append(self.node0)
        self.command_buff = []
        self.sess = sess()
        self.openPort()
        serialport(self)

    #TODO unfinished
    def refreshDevices(self):
        '''
        Refreshes the network devices by sending a broadcast status command to the network.
        All devices on the network will respond with their status.
        '''
        self.node_list = [] # Clear the list of connected nodes... should this be done?
        broadcast_node = node(0, self)
        broadcast_node.addr = [0xFF,0xFF,0xFF]  # Broadcast address
        command_t(broadcast_node, name = "status", params = [1])  # How to send command to all nodes without creating a new node object?
        send_command()
        # Await for responses. should this be blocking with a timeout?
        # If blocking, then we know that the device list is updated when the function returns.
        
    def addNode(self): # change later for incorporating nodes
        node0 = node(len(node.nodel)+1,self)
        node0.addr = [0x04,0x05,0x06]
        self.node_list.append(node0)
    
    def getDevice(self,addr):
        
        for x in self.node_list:
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
           
    def disperse(self,rec_cmd):
        for node in self.node_list:
            if node.addr == rec_cmd[0]:
                node.lastcmd = deconstructor(rec_cmd[1])
                self.sess.logging(rec_cmd[1],1)
                break

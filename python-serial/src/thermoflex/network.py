from .tools.nodeserial import serial_thread, send_command
from .tools.packet import command_t, deconst_response_packet
from .devices import Node, muscle
from .sessions import session
from .controls import debug, DEBUG_LEVELS
import serial as s
import time as t
#TODO: id address pull from network
def sess(net):#create session if one does not exist
    if session.sescount>0:
        return session.sessionl[0]
    else:
        return session(net)
class NodeNet:
    
    netlist = [] # Static list of all nodenet objects
    def __init__(self, idnum, port):
        NodeNet.netlist.append(self)
        self.idnum = idnum
        self.port = port
        self.arduino = None
        self.broadcast_node = Node(0,self)
        self.node0 = Node(1, self)
        self.broadcast_node.node_id = [0xFF,0xFF,0xFF]
        self.node0.node_id = [0x00,0x00,0x01]
        self.node_list = [] # list of connected nodes
        self.node_list.extend([self.broadcast_node,self.node0])
        self.command_buff = []
        self.sess = sess(self)
        self.openPort()
        self.debug_name = f"NodeNet {self.idnum}" # Name for debugging purposes
        serial_thread(self)
        
    def refreshDevices(self):
        '''
        Refreshes the network devices by sending a broadcast status command to the network.
        All devices on the network will respond with their status.
        '''
        #self.node_list = [] # Clear the list of connected nodes... should this be done?
        self.broadcast_node.status('dump') #broadcasts status to all devices
        t.sleep(0.1) # Await for responses
        # If blocking, then we know that the device list is updated when the function returns.
    
    def addNode(self, node_id):
        node_id = [int(x) for x in node_id] # In case node_id is a byte array
        debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Adding node: {node_id}")
        new_node = Node(len(Node.nodel)+1,self)
        new_node.node_id = node_id
        self.node_list.append(new_node)
        return new_node
    
    def removeNode(self, node_id):
        node_id = [int(x) for x in node_id] # In case node_id is a byte array
        debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Removing node: {node_id}")
        for node in self.node_list:
            if node.node_id == node_id:
                self.node_list.remove(node)

    def getDevice(self, node_id):
        
        for x in self.node_list:
            debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Checking node: {x.node_id} with {node_id}")
            if node_id == x.node_id:
                return x
            else:
                pass
    
        debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Node: {node_id} not found in {self.debug_name}")

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
                debug(DEBUG_LEVELS['ERROR'], self.debug_name, "Error: Serial not opened, check port status")
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
           debug(DEBUG_LEVELS['ERROR'], self.debug_name, "Error: Serial not closed")
           
    # Disperse incoming response packets to the appropriate node manager object, based on the sender_id
    def disperse(self, rec_packet):
        debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Dispersing packet: {rec_packet}")
        packet_node_id = [int(x) for x in rec_packet['sender_id']] # Node ID is stored as a list of integers
        response = deconst_response_packet(rec_packet['payload'])
        matching_node = None

        # Check if the node already exists in the network
        for node in self.node_list:# TODO: Disperse packet to node or muscle accordingly
            if node.node_id == packet_node_id:
                matching_node = node
                debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Packet dispersing to existing node with id: {node.node_id}")
                return
            
        # If the node does not exist in the network, add it
        if(matching_node == None):  
            matching_node = self.addNode(packet_node_id)
            debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Packet dispersing to new node with id: {packet_node_id}")

        # Disperse the response to the node
        if 'status' in response:
            matching_node.status_curr = response
        else:
            matching_node.latest_resp = response

        debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Dispersed packet to node: {matching_node.node_id}")

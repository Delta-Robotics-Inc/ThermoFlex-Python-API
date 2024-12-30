from .tools.nodeserial import serial_thread, send_command
from .tools.packet import command_t, deconst_serial_response
from .devices import Node, Muscle
from .sessions import Session
from .tools.debug import Debugger as D, DEBUG_LEVELS
import serial as s
import time as t
#TODO: id address pull from network
def sess(net):#create session if one does not exist
    if Session.sescount>0:
        return Session.sessionl[-1]
    else:
        return Session(net)
class NodeNet:
    
    netlist = [] # Static list of all nodenet objects
    def __init__(self, idnum, port):
        NodeNet.netlist.append(self)
        self.idnum = idnum
        self.port = port
        self.arduino = None
        self.broadcast_node = Node(0,self)
        self.self_node = Node(1, self)
        self.broadcast_node.node_id = [0xFF,0xFF,0xFF]
        self.self_node.node_id = [0x00,0x00,0x01]
        self.node_list = [] # list of connected nodes; leave broadcast node and self-node out of list
        self.command_buff = []
        self.sess = sess(self)
        self.openPort()
        self.debug_name = f"NodeNet {self.idnum}" # Name for debugging purposes
        self.refreshDevices()
        self.start_serial()
        
    def refreshDevices(self):
        '''
        Refreshes the network devices by sending a broadcast status command to the network.
        All devices on the network will respond with their status.
        '''
        #self.node_list = [] # Clear the list of connected nodes... should this be done?
        self.broadcast_node.status('compact') #broadcasts status to all devices
        t.sleep(0.1) # Await for responses
        # If blocking, then we know that the device list is updated when the function returns.
    
    def addNode(self, node_id):
        node_id = [int(x) for x in node_id] # In case node_id is a byte array
        D.debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Adding node: {node_id}")
        new_node = Node(len(Node.nodel)+1,self)
        new_node.node_id = node_id
        self.node_list.append(new_node)
        return new_node
    
    def removeNode(self, node_id):
        node_id = [int(x) for x in node_id] # In case node_id is a byte array
        D.debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Removing node: {node_id}")
        for node in self.node_list:
            if node.node_id == node_id:
                self.node_list.remove(node)

    def getDevice(self, node_id):
        # Helper function to convert an integer to a byte list
        def int_to_bytearray(n):
            return list(n.to_bytes((n.bit_length() + 7) // 8, byteorder='big')) or [0]

        # If node_id is an integer, convert it to a byte list
        if isinstance(node_id, int):
            node_id = int_to_bytearray(node_id)
        
        for x in self.node_list:
            D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Checking node: {x.node_id} with {node_id}")
            if node_id == x.node_id:
                return x
            else:
                continue
    
        D.debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Node: {node_id} not found in {self.debug_name}")

    def nodeonNet(self): #periodically sends network
        command_t(self.self_node, name = "status", params = [1])
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
                D.debug(DEBUG_LEVELS['ERROR'], self.debug_name, "Error: Serial not opened, check port status")
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
           D.debug(DEBUG_LEVELS['ERROR'], self.debug_name, "Error: Serial not closed")

    def start_serial(self):
        serial_thread(self)           
    # Disperse incoming response packets to the appropriate node manager object, based on the sender_id
    def disperse(self, rec_packet):
        D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Dispersing packet: {rec_packet}")
        packet_node_id = rec_packet['sender_id']# Node ID is stored as a list of integers
        response = deconst_serial_response(rec_packet['payload'])
        matching_node = None

        # Check if the node already exists in the network
        for node in self.node_list:# TODO: Disperse packet to node or muscle accordingly
            if node.node_id == packet_node_id:
                matching_node = node
                D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Packet dispersing to existing node with id: {node.node_id}")
                break
            
        # If the node does not exist in the network, add it
        if(matching_node == None):  
            matching_node = self.addNode(packet_node_id)
            D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Packet dispersing to new node with id: {packet_node_id}")

        # Disperse the response to the node
        if 'status' in response[0]:
            matching_node.updateStatus(response)
        else:
            matching_node.latest_resp = response[1]

        D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Dispersed packet to node: {matching_node.node_id}")

from .tools.nodeserial import serial_thread, send_command, stop_threads_flag, threaded
from .tools.packet import command_t, deconst_serial_response
from .devices import Node, Muscle
from .sessions import Session
from .tools.debug import Debugger as D, DEBUG_LEVELS
import serial as s
import time as t
import threading as thr
#TODO: id address pull from network

NET_MANAGER_FLAG = thr.Event()

class NetManager:
    
    manage_list = []
    def __init__(self, net = None):
        NetManager.manage_list.append(net)
        NET_MANAGER_FLAG.clear()
        NetManager.net_manager_thread()
    
    def add_net(net):
        NetManager.manage_list.append(net)

    def remove_net(net):
        NetManager.manage_list.remove(net)

    def stop_manager():
        NET_MANAGER_FLAG.set()

    @threaded
    def net_manager_thread():
        
        while NET_MANAGER_FLAG.is_set() == False:
            
            checklist = NodeNet.netlist.copy()
            for net in checklist:
                # for cmd in net.rec_cmd_buff:
                #     net.disperse(cmd)
                #     del net.rec_cmd_buff[cmd]
                
                try:
                    net.update_network()
                except TypeError:
                    pass

def sess(net):#create session if one does not exist
    if Session.sescount>0:
        return Session.sessionl[-1]
    else:
        return Session(net)

def manager(net): #create a manager if one does not exist
    if len(NetManager.manage_list) != 0:
        NetManager.add_net(net)
    else:
        NetManager(net)

class NodeNet:
    
    netlist = [] # Static list of all nodenet objects
    TIMEOUT = 99
    def __init__(self, idnum, port):
        NodeNet.netlist.append(self)
        self.idnum = idnum
        self.port = port
        self.arduino = None
        self.broadcast_node = Node(0,self, n_id=[0xFF,0xFF,0xFF],pulse=False)
        self.self_node = Node(1, self, n_id=[0x00,0x00,0x01],pulse = False)
        self.node_list = [] # list of connected nodes; leave broadcast node and self-node out of list
        self.command_buff = []
        self.rec_cmd_buff = []
        self.sess = sess(self)
        self.manager = manager(self)
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
        new_node = Node(len(Node.nodel)+1,self, n_id=node_id)
        self.node_list.append(new_node)
        return new_node
    
    def removeNode(self, node_id):
        node_id = [int(x) for x in node_id] # In case node_id is a byte array
        D.debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Removing node: {node_id}")
        for node in self.node_list:
            if node.node_id == node_id:
                self.node_list.remove(node)
                node.endself()

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
        node_l = self.node_list.copy()
        response = deconst_serial_response(rec_packet['payload'])
        matching_node = None
        print(self.node_list, node_l, packet_node_id) #TEST
        # Check if the node already exists in the network
        
        for node in node_l:# TODO: Disperse packet to node or muscle accordingly
            if node.node_id == packet_node_id:
                matching_node = node
                print("matching node found") #TEST
                D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Packet dispersing to existing node with id: {node.node_id}")
                break
        else: # If the node does not exist in the network, add it     
            matching_node = self.addNode(packet_node_id)
            #print(self.node_list, node_l, packet_node_id) #TEST
            # try:
            #     matching_node = self.getDevice(packet_node_id)
            # except IndexError:
            #     print("Node {packet_node_id} not added.")
            
            D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Packet dispersing to new node with id: {packet_node_id}")
            
        #print(self.node_list, node_l, packet_node_id) #TEST
        matching_node.msgrec = True

        if 'status' in response[0]:
            matching_node.updateStatus(response)
        else:
            matching_node.latest_resp = response[1]
        
        D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Dispersed packet to node: {matching_node.node_id}")
    
    def update_node(self,id):

        #gets node device
        node = self.getDevice(id)
        
        #checks node status and updates times
        if node.msgsent == True:
            node.tlastmsgsent = int(t.time())
            node.msgsent == False
        
        if node.msgrec == True:
            node.tlastmsgrec = int(t.time())
            node.msgrec == False

    def time_check(self):

        currtime = int(t.time())
        for node in self.node_list:
            if node.heartbeat == True:
                if (node.tlastmsgrec + 1) > NodeNet.TIMEOUT:
                    node.endself()

                if node.tlastmsgsent > NodeNet.TIMEOUT:
                    send_command(node.pulse, self)

    def update_network(self):

        for node in self.node_list:
            self.update_node(node.node_id)
        self.time_check()
             
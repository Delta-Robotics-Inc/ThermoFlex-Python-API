from .tools.nodeserial import serial_thread, send_command
from .tools.packet import command_t, deconst_response_packet
from .devices import Node, muscle
from .sessions import session
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
        print(f"Adding node: {node_id}")
        new_node = Node(len(Node.nodel)+1,self)
        new_node.node_id = node_id
        self.node_list.append(new_node)
    
    def removeNode(self, node_id):
        node_id = [int(x) for x in node_id] # In case node_id is a byte array
        print(f"Removing node: {node_id}")
        for node in self.node_list:
            if node.node_id == node_id:
                self.node_list.remove(node)

    def getDevice(self, node_id):
        
        for x in self.node_list:
            print(f"Checking node: {x.node_id} with {node_id}")
            if node_id == x.node_id:
                return x
            else:
                pass
    
        print(f'Node: {node_id} not found in network: {self.idnum}')

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
           
    # Disperse incoming response packets to the appropriate node manager object, based on the sender_id
    def disperse(self, rec_packet):
        print("Dispersing packet")
        response = deconst_response_packet(rec_packet['payload'])
        for node in self.node_list:# TODO: Disperse packet to node or muscle accordingly
            if node.node_id == rec_packet['sender_id']:
                if 'status' in  response:
                    node.status_curr = response
                else:
                    node.latest_resp = response
                #self.sess.logging(rec_cmd[1],1)
                print(f"Packet dispersed to existing node with id: {node.node_id}")
                return
        
        existing_node = None
        for node in self.node_list:
            if node.node_id == rec_packet['sender_id']:
                existing_node = node
                break
        
        if existing_node:
            # Handle existing node
            if 'status' in response:
                existing_node.status_curr = response
            else:
                existing_node.latest_resp = response
            print(f"Packet dispersed to existing node with id: {rec_packet['sender_id']}")
        else:
            # Handle new node
            try:
                print("Adding new node to network")
                self.addNode(rec_packet['sender_id'])
                # After adding, we should also update its status if this is a status packet
                new_node = self.getDevice(rec_packet['sender_id'])
                if new_node:
                    if 'status' in response:
                        new_node.status_curr = response
                    else:
                        new_node.latest_resp = response
                print(f"Packet dispersed to new node with id: {rec_packet['sender_id']}")
            except Exception as e:
                print(f"Error: Could not add node: {str(e)}")
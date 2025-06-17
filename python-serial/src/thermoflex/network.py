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
        """Thread that manages all networks and ensures heartbeats are sent"""
        D.debug(DEBUG_LEVELS['INFO'], "NetManager", "Network manager thread started")
        
        while not NET_MANAGER_FLAG.is_set():
            try:
                checklist = NodeNet.netlist.copy()
                for net in checklist:                
                    try:
                        net.update_network()
                        D.debug(DEBUG_LEVELS['DEBUG'], "NetManager", f"Updated network {net.idnum}")
                    except Exception as e:
                        D.debug(DEBUG_LEVELS['ERROR'], "NetManager", f"Error updating network {net.idnum}: {e}")
                        
                if stop_threads_flag.is_set():
                    NET_MANAGER_FLAG.set()
                    break
                    
                # Sleep for a shorter interval to ensure more frequent heartbeat checks
                t.sleep(0.5)  # Check every 500ms instead of blocking
                
            except Exception as e:
                D.debug(DEBUG_LEVELS['ERROR'], "NetManager", f"Error in network manager thread: {e}")
                t.sleep(1.0)
        
        D.debug(DEBUG_LEVELS['INFO'], "NetManager", "Network manager thread ended")

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
    """
    Network Manager class for Thermoflex devices.
    
    The NodeNet class is responsible for managing the network of Thermoflex nodes connected via USB serial.
    It handles all network-level operations including:
    - Node lifecycle management (creation, activation, deactivation)
    - Network communication and packet distribution
    - Heartbeat system management
    - Node status tracking and cleanup
    - Serial port management
    
    The class maintains two node collections:
    - active_nodes: Dictionary of currently active nodes, keyed by node ID
    - inactive_nodes: Dictionary of inactive/forgotten nodes, keyed by node ID
    
    Attributes:
        netlist (list[NodeNet]): Static list of all NodeNet instances
        TIMEOUT (int): Default timeout for node operations
        HEARTBEAT_INTERVAL (float): Interval between broadcast heartbeats
        NODE_CLEANUP_INTERVAL (float): Interval between node cleanup checks
        
    Network Management:
        - Manages node lifecycle (creation, activation, deactivation)
        - Handles network communication and packet distribution
        - Maintains node status and connectivity
        - Manages broadcast and self nodes
        - Handles serial port operations
        
    Communication:
        - Processes incoming packets
        - Distributes commands to appropriate nodes
        - Manages command buffering
        - Handles heartbeat system
        
    Node Management:
        - Tracks active and inactive nodes
        - Manages node cleanup and reactivation
        - Handles node status updates
        - Maintains node connectivity
    """
    netlist: list['NodeNet'] = [] # Static list of all nodenet objects
    TIMEOUT = 99
    HEARTBEAT_INTERVAL = 2.0  # Interval between broadcast heartbeats in seconds (reduced from 1.0 to 2.0 to match firmware expectations better)
    NODE_CLEANUP_INTERVAL = 5.0  # Interval between node cleanup checks in seconds

    def __init__(self, idnum, port):
        NodeNet.netlist.append(self)
        self.idnum = idnum
        self.port = port
        self.arduino = None
        self.debug_name = f"NodeNet {self.idnum}"  # Initialize debug_name first
        
        # Network management
        self.active_nodes: dict[tuple, 'Node'] = {}  # Dict of active nodes, keyed by node ID tuple
        self.inactive_nodes: dict[tuple, 'Node'] = {}  # Dict of inactive nodes, keyed by node ID tuple
        self.broadcast_node = Node(0, self, n_id=[0xFF,0xFF,0xFF], pulse=False)
        self.self_node = Node(1, self, n_id=[0x00,0x00,0x01], pulse=False)
        
        # Network state
        self.command_buff = []
        self.rec_cmd_buff = []
        self.last_heartbeat_time = 0
        self.last_cleanup_time = 0
        
        # Network services
        self.sess = sess(self)
        self.manager = manager(self)
        
        try:
            self.open_port()  # Changed from openPort to open_port for consistency
        except Exception as e:
            D.debug(DEBUG_LEVELS['ERROR'], self.debug_name, f"Failed to open port: {e}")
            raise
        self.refreshDevices()
        self.start_serial()

    @property
    def node_list(self) -> list['Node']:
        """
        Property to maintain backward compatibility with code expecting node_list.
        Returns a list of active nodes.
        """
        return list(self.active_nodes.values())

    def open_port(self):
        """Open the serial port for this network"""
        try:
            self.arduino = s.Serial(self.port, 115200, timeout=0.1)
            D.debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Opened port {self.port}")
        except s.SerialException as e:
            D.debug(DEBUG_LEVELS['ERROR'], self.debug_name, f"Failed to open port {self.port}: {e}")
            raise

    def close_port(self):
        """Close the serial port for this network"""
        try:
            if self.arduino and self.arduino.is_open:
                self.arduino.close()
                D.debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Closed port {self.port}")
        except s.SerialException as e:
            D.debug(DEBUG_LEVELS['WARNING'], self.debug_name, f"Error closing port {self.port}: {e}")

    def add_node(self, node_id: list[int]) -> 'Node':
        """
        Add a new node to the network.
        Args:
            node_id: List of integers representing the node's ID
        Returns:
            Node: The newly created node object
        """
        node_id_tuple = tuple(node_id)  # Convert to tuple for dictionary key
        if node_id_tuple in self.active_nodes:
            return self.active_nodes[node_id_tuple]
            
        if node_id_tuple in self.inactive_nodes:
            # Reactivate existing inactive node
            node = self.inactive_nodes.pop(node_id_tuple)
            node.reactivate()
            self.active_nodes[node_id_tuple] = node
            return node
            
        # Create new node
        node = Node(len(self.active_nodes) + 1, self, n_id=node_id)
        self.active_nodes[node_id_tuple] = node
        D.debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Added new node with ID {node_id}")
        return node

    def remove_node(self, node_id: list[int], deactivate: bool = True):
        """
        Remove a node from the network.
        Args:
            node_id: List of integers representing the node's ID
            deactivate: If True, move to inactive nodes, if False, remove completely
        """
        node_id_tuple = tuple(node_id)
        if node_id_tuple in self.active_nodes:
            node = self.active_nodes.pop(node_id_tuple)
            if deactivate:
                self.inactive_nodes[node_id_tuple] = node
                node.deactivate()
            else:
                node.cleanup()
            D.debug(DEBUG_LEVELS['INFO'], self.debug_name, f"Removed node with ID {node_id}")

    def get_node(self, node_id: list[int]) -> 'Node':
        """
        Get a node by its ID.
        Args:
            node_id: List of integers representing the node's ID
        Returns:
            Node: The node object if found, None otherwise
        """
        node_id_tuple = tuple(node_id)
        return self.active_nodes.get(node_id_tuple)

    def get_all_nodes(self) -> list['Node']:
        """Get all active nodes in the network"""
        return list(self.active_nodes.values())

    def get_inactive_nodes(self) -> list['Node']:
        """Get all inactive nodes in the network"""
        return list(self.inactive_nodes.values())

    def cleanup_inactive_nodes(self):
        """Check and cleanup inactive nodes"""
        current_time = t.time()
        if current_time - self.last_cleanup_time >= self.NODE_CLEANUP_INTERVAL:
            nodes_to_check = list(self.active_nodes.values())
            for node in nodes_to_check:
                if not node.check_heartbeat_status():
                    self.remove_node(node.id, deactivate=True)
            self.last_cleanup_time = current_time

    def disperse(self, rec_packet):
        """Process received packets including heartbeat responses"""
        D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Dispersing packet: {rec_packet}")
        packet_node_id = rec_packet['sender_id']
        response = deconst_serial_response(rec_packet['payload'])
        
        # Check if this is a heartbeat response
        if 'heartbeat' in response[0]:
            self.process_node_heartbeat(packet_node_id)
            return

        # Handle other packet types
        node = self.get_node(packet_node_id)
        if not node:
            node = self.add_node(packet_node_id)
            
        node.msgrec = True
        if 'status' in response[0]:
            node.updateStatus(response)
        else:
            node.latest_resp = response[1]
        
        D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Dispersed packet to node: {node.id}")

    def end_network(self):
        """Clean up all network resources"""
        # Disable all nodes
        for node in self.get_all_nodes():
            node.disableAll()
            t.sleep(0.1)
        
        # Close all node connections
        for node in self.get_all_nodes():
            node.cleanup()
        
        # Clear node lists
        self.active_nodes.clear()
        self.inactive_nodes.clear()
        
        # Close network port
        try:
            self.close_port()  # Changed from closePort to close_port
        except s.SerialException:
            D.debug(DEBUG_LEVELS['WARNING'], self.debug_name, "Warning: Port not open but attempted to close")
        
        # Remove from network list
        if self in NodeNet.netlist:
            NodeNet.netlist.remove(self)

    def refreshDevices(self):
        '''
        Refreshes the network devices by sending a broadcast status command to the network.
        All devices on the network will respond with their status.
        '''
        self.broadcast_node.status('compact')  # broadcasts status to all devices
        # Note: The node_list property will automatically reflect any changes to active_nodes

    def start_serial(self):
        serial_thread(self)           
    # Disperse incoming response packets to the appropriate node manager object, based on the sender_id
    def update_node(self, id):
        """Update node status and message tracking"""
        node = self.get_node(id)
        if not node:
            return
            
        current_time = int(t.time())
        if node.msgsent:
            node.tlastmsgsent = current_time
            node.msgsent = False  # Fixed boolean assignment
        
        if node.msgrec:
            node.tlastmsgrec = current_time
            node.msgrec = False  # Fixed boolean assignment

    def time_check(self):
        """
        Manages the heartbeat system for all nodes in the network.
        For each node with heartbeat enabled:
        1. Checks if we haven't received a message within TIMEOUT period
        2. Checks if we haven't sent a heartbeat within TIMEOUT period
        If either condition is met, appropriate action is taken (node removal or heartbeat send)
        """
        current_time = int(t.time())
        for node in self.get_all_nodes():
            if not node.heartbeat:
                continue
                
            # Check if we haven't received a message from the node within TIMEOUT period
            if node.tlastmsgrec is not None and (current_time - node.tlastmsgrec) >= self.TIMEOUT:
                D.debug(DEBUG_LEVELS['WARNING'], self.debug_name, f"Node {node.id} timed out - no messages received")
                self.remove_node(node.id, deactivate=True)
                continue

            # Check if we haven't sent a heartbeat to the node within TIMEOUT period
            if node.tlastmsgsent is not None and (current_time - node.tlastmsgsent) >= self.TIMEOUT:
                D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Sending heartbeat to node {node.id}")
                send_command(node.pulse, self)

    def send_broadcast_heartbeat(self):
        """Send a broadcast heartbeat to all nodes in the network"""
        current_time = t.time()
        if current_time - self.last_heartbeat_time >= self.HEARTBEAT_INTERVAL:
            # Create and send broadcast heartbeat command
            heartbeat_cmd = command_t(self.broadcast_node, name="heartbeat", params=[])
            self.command_buff.append(heartbeat_cmd)
            self.last_heartbeat_time = current_time
            D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Broadcast heartbeat sent at {current_time}")
            
            # Also update individual node heartbeat tracking
            for node in self.get_all_nodes():
                if hasattr(node, 'update_heartbeat'):
                    node.update_heartbeat(received=False)  # Mark that we sent a heartbeat

    def process_node_heartbeat(self, node_id):
        """Process a heartbeat received from a node"""
        node = self.get_node(node_id)
        if node:
            node.update_heartbeat(received=True)
            D.debug(DEBUG_LEVELS['DEBUG'], self.debug_name, f"Heartbeat received from node {node_id} at {t.time()}")
        else:
            D.debug(DEBUG_LEVELS['WARNING'], self.debug_name, f"Received heartbeat from unknown node {node_id}")

    def update_network(self):
        """Update network status including heartbeat management"""
        # Send broadcast heartbeat if needed - this is the key method that needs to be called regularly
        self.send_broadcast_heartbeat()
        
        # Clean up inactive nodes
        self.cleanup_inactive_nodes()
        
        # Update node statuses
        for node in self.get_all_nodes():
            self.update_node(node.id)
             
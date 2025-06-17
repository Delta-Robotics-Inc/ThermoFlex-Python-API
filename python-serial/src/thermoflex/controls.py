from .network import NodeNet
from .devices import Node
from .sessions import Session
from .tools.nodeserial import stop_threads_flag, threadlist, threaded
from .tools.debug import Debugger as D, DEBUG_LEVELS
import serial as s
import serial.tools.list_ports as stl
import time as t
import sys
import platform
import os
import threading
prod = [105] # Product id list

#-----------------------------------------------------------------------------------------------------------

# Wrapper functions for the debugger class
def set_debug_level(level):
    D.set_debug_level(level)

#TODO: put a rediscover in discover, have discover check for existing serial numbers      

# Check permissions for Linux and warn the user if they are incorrectly set

def check_serial_permissions():
    if platform.system() == "Linux":
        YELLOW = "\033[33m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        import grp
        try:
            dialout_gid = grp.getgrnam("dialout").gr_gid
            user_groups = os.getgroups()
            if dialout_gid not in user_groups:
                print(f"{YELLOW}Warning: Your user is not in the 'dialout' group. "
                      f"Please run:\n\n  sudo usermod -aG dialout $USER\n\n"
                      f"and {BOLD}log out/in again{RESET}{YELLOW} to grant access to serial ports.{RESET}")
        except KeyError:
            print(f"{YELLOW}Warning: The 'dialout' group does not exist on your system. "
                  f"You may need to adjust device permissions manually.{RESET}")



def discover(proid = prod) -> list[NodeNet]: 
    """
    Discover Thermoflex nodes on available USB ports.
    
    Args:
        proid (list[int]): List of USB product IDs to search for
        
    Returns:
        list[NodeNet]: List of discovered NodeNet instances
        
    Raises:
        ImportError: If no nodes are found
    """
    check_serial_permissions()  # Gives a warning to the user if they are not in dialout group
    
    ports = {}
    discovered_nets = []
    
    # Scan available ports
    for por in stl.comports(include_links=False):
        # Debug all found ports
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"Device: {por.device}")
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"|  PID: {por.pid}")
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"|  VID: {por.vid}")
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"|  Serial Number: {por.serial_number}")
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"|  Description: {por.description}")

        ports[por.pid] = [por.device, por.serial_number]  # Linux requires por.device but windows is ok with por.name
        
    # Create networks for matching ports
    for pid in proid:
        if pid in ports:
            try:
                net = NodeNet(len(NodeNet.netlist) + 1, ports[pid][0])
                discovered_nets.append(net)
                D.debug(DEBUG_LEVELS['INFO'], "discover", f"Created network for device at {ports[pid][0]}")
            except Exception as e:
                D.debug(DEBUG_LEVELS['ERROR'], "discover", f"Failed to create network for device at {ports[pid][0]}: {e}")
                continue
    
    if not discovered_nets:
        raise ImportError('No Thermoflex nodes found on available USB ports')
        
    return discovered_nets


# Helper function for single node discovery
def get_usb_node(bus_id=105, timeout=5.0, poll_interval=0.1):
    """
    Discover USB network and return the first available node, waiting up to `timeout` seconds.

    Args:
        bus_id (int): USB bus ID to search.
        timeout (float): Maximum time in seconds to wait for a device.
        poll_interval (float): Interval between checks in seconds.

    Returns:
        Node object if found, else raises TimeoutError.
    """
    node_net = discover([bus_id])[0]
    node_net.refreshDevices()

    start_time = t.time()
    while t.time() - start_time < timeout:
        # Check active_nodes instead of node_list
        active_nodes = list(node_net.active_nodes.values())
        if active_nodes:
            print(f"Found node on USB bus at port {node_net.port}")
            return active_nodes[0]  # Return first active node
        t.sleep(poll_interval)

    raise TimeoutError(f"No nodes discovered on USB bus {bus_id} within {timeout} seconds.")

     
#------------------------------------------------------------------------------------

# @threaded
# def timer(time):# TODO: seperate event flag f
#     global timeleft
#     timeleft = time
#     for x in range(time):
#         timeleft-=1
#         t.sleep(1)
#     if stop_threads_flag.is_set: return    
#     else:
#         stop_threads_flag.clear()

# def update():
#     '''
    
#     Updates all networks in the list to send commands and receive data
    
#     '''  
#     for net in NodeNet.netlist:
#         net.refreshDevices()

# def updatenet(network:object): #choose which node to update and the delay
#     '''
    
#     Updates a specific network.
    
#     '''  
#     network.refreshDevices()
        
# def delay(time):
#     global timeleft
#     timeleft = time
#     while timeleft > 0:
#         timeleft -= 1
#         for net in NodeNet.netlist:
#             updatenet(net)
#         t.sleep(1)

def delay(time):
    print("tf.delay() is deprecated. Use time.sleep() instead.")
    t.sleep(time)
        
def endsession(session:object):
    session.end()
    del session

def endAll():
    """
    Closes all node ports and ends all threads.
    """

    # Disable all nodes (allow time for messages to be sent)
    for net in NodeNet.netlist:
        for node in net.get_all_nodes():
            node.disableAll()
            t.sleep(0.1)
    
    # Signal threads to stop
    stop_threads_flag.set()
    
    # Wait for all threads to finish
    for th in threadlist:
        th.join()
    
    D.debug(DEBUG_LEVELS['INFO'], "endAll", "All threads have been closed")
    
    # Close all node ports and clean up networks
    for net in NodeNet.netlist:
        try:
            net.close_port()
        except s.SerialException:
            D.debug(DEBUG_LEVELS['WARNING'], "endAll", "Warning: Port not open but attempted to close")
        finally:
            net.end_network()
    
    # Clean up session lists
    for sess in Session.sessionl:
        sess.end()
        del sess

    sys.exit()  # End program (adjust if you need the program to continue)


    
#----------------------------------------------------------------------------------------------------------------------------

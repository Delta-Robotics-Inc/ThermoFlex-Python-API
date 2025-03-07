
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



def discover(proid = prod): 
    '''
    
    Takes node-object idnumber and tries to find corresponding port.
    
    '''

    check_serial_permissions()  # Gives a warning to the user if they are not in dialout group
    
    ports = {}
    
    z = len(NodeNet.netlist)

    for por in stl.comports(include_links=False):
        # Debug all found ports
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"Device: {por.device}")
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"|  PID: {por.pid}")
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"|  VID: {por.vid}")
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"|  Serial Number: {por.serial_number}")
        D.debug(DEBUG_LEVELS['DEBUG'], "discover", f"|  Description: {por.description}")

        ports[por.pid]= [por.device, por.serial_number]  # Linux requires por.device but windows is ok with por.name
        
    for p in proid:
        for key in ports.keys():
            if p == key:
                nodenetw = NodeNet(z+1, ports[key][0])
                #nodenetw.openPort()
                #nodenetw.closePort()
                z+=1
    if z == 0:
        raise ImportError('There are no connected nodes.')
    else:
        return NodeNet.netlist
     
#------------------------------------------------------------------------------------

@threaded
def timer(time):# TODO: seperate event flag f
    global timeleft
    timeleft = time
    for x in range(time):
        timeleft-=1
        t.sleep(1)
    stop_threads_flag.clear()

def update():
    '''
    
    Updates all networks in the list to send commands and receive data
    
    '''  
    for net in NodeNet.netlist:
        net.refreshDevices()

def updatenet(network:object): #choose which node to update and the delay
    '''
    
    Updates a specific network.
    
    '''  
    network.refreshDevices()
        
def delay(time):
    global timeleft
    timeleft = time
    while timeleft > 0:
        timeleft -= 1
        for net in NodeNet.netlist:
            updatenet(net)
        t.sleep(1)
        
def endsession(session:object):
    session.end()
    del session

def endAll():
    """
    Closes all node ports and ends all threads.
    """

    # Disable all nodes (allow time for messages to be sent)
    for node in Node.nodel:
        node.disableAll()
        t.sleep(0.1)
    
    # Signal threads to stop
    stop_threads_flag.set()
    
    # Wait for all threads to finish
    for th in threadlist:
        th.join()
    
    D.debug(DEBUG_LEVELS['INFO'], "endAll", "All threads have been closed")
    
    # Close all node ports
    for node in Node.nodel:
        try:
            node.net.closePort()
        except s.SerialException:
            D.debug(DEBUG_LEVELS['WARNING'], "endAll", "Warning: Port not open but attempted to close")
        finally:
            del node
    
    # Clean up network and session lists
    for net in NodeNet.netlist:
        del net

    for sess in Session.sessionl:
        sess.end()
        del sess

    sys.exit()  # End program (adjust if you need the program to continue)


    
#----------------------------------------------------------------------------------------------------------------------------

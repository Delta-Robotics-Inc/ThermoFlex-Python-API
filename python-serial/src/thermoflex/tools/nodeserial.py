import sys
import serial as s
import time as t
import struct as st

from .packet import parse_packet, command_t, STARTBYTE
from .debug import Debugger as D, DEBUG_LEVELS
import threading as thr
from enum import Enum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..network import NodeNet  # Only imported for type checking

# ANSI color codes
GRAY = "\033[90m"  # Bright black/gray color
RESET = "\033[0m"  # Reset color

stop_threads_flag = thr.Event() # Flag to stop all threads when the thread is ready to close

def threaded(func):
    global threadlist
    threadlist = []
    
    def wrapper(*args, **kwargs):
        thread = thr.Thread(target=func, args=args, kwargs = kwargs)
        thread.start()
        #print(thread.getName(),func) # prints thread name and function type
        threadlist.append(thread)
        return thread

    return wrapper

def send_command_str(command, network): #TODO: construct packet in commmand, remove send_command options
    '''
    
    Prints the command to a terminal. Used for test purposes.
    
    '''
    port = network.arduino
 
    command_final = b''
    for c in command.packet:
        if type(c) == str:
            command_final += bytes(c,'ascii')
        elif type(c) == int:
            command_final += st.pack('!B', c)
        elif type(c) == bytes:
            command_final += c
    
    # Use the debug function to print the command packet to the terminal
    D.debug(DEBUG_LEVELS['INFO'], "send_command_str", f'\nPort: {port}')
    D.debug(DEBUG_LEVELS['INFO'], "send_command_str", f'Command Packet: {command.packet}')
    D.debug(DEBUG_LEVELS['INFO'], f'{command_final}\n')
    
    t.sleep(0.05)

def send_command(command, network):
    """
    Send a command to a node through the network.
    
    Args:
        command: Command object to send
        network: NodeNet instance to send through
    """
    try:
        port = network.arduino
        D.debug(DEBUG_LEVELS['DEBUG'], "send_command", f'Sent Command{command.packet}')
        
        # Generate the packet and send it
        if hasattr(command, 'packet'):
            port.write(bytearray(command.packet))
        elif hasattr(command, 'generate'):
            port.write(command.generate())
        else:
            D.debug(DEBUG_LEVELS['ERROR'], "Serial", f"Command object has no packet or generate method")
            return False
        
        t.sleep(0.05)
        
        # Update node status if it's not a broadcast
        if not (command.destnode_id == [0xFF,0xFF,0xFF] or command.destnode_id == [0x00,0x00,0x01]):
            node = network.get_node(command.destnode_id)
            if node:
                node.msgsent = True
                if hasattr(node, 'update_heartbeat'):
                    node.update_heartbeat(received=False)
        
        return True
    except Exception as e:
        D.debug(DEBUG_LEVELS['ERROR'], "Serial", f"Error sending command: {e}")
        return False

# States for the receiver state machine
class ReceptionState(Enum):
    WAIT_FOR_START_BYTE = 1
    READ_LENGTH = 2
    READ_PACKET = 3


# Receives data from a Node Network's serial port and processes packets
class Receiver:
    def __init__(self, network):
        self.state = ReceptionState.WAIT_FOR_START_BYTE
        self.packetData = bytearray()
        self.packetLength = 0
        self.network = network
        self.node_debug_str = ""

    def receive(self):
        port = self.network.arduino

        # Check if port is still open before attempting to read
        if not port.is_open:
            return None

        #try:
        if port.in_waiting > 0:
            D.debug(DEBUG_LEVELS['DEBUG'], "SerialThread", f"\n{GRAY}Reading incoming data from network {self.network.idnum}:{RESET}")
        elif len(self.node_debug_str) > 0: # If there is no incoming data, but there is debug data, print the debug data
            D.debug_raw(DEBUG_LEVELS['DEVICE'], f"{GRAY}{self.node_debug_str}{RESET}")
            self.node_debug_str = ""
        while port.in_waiting > 0:
            
            # Check if the stop_threads_flag has been set, if so, break the loop and end the thread
            if stop_threads_flag.is_set():
                break
            
            try:
                byte = port.read(1)
                byte = byte[0]  # Convert from bytes to integer
            except TypeError:
                continue  # Ignore invalid bytes

            if self.state == ReceptionState.WAIT_FOR_START_BYTE:
                if byte == STARTBYTE:
                    D.debug(DEBUG_LEVELS['DEVICE'], "SerialThread", f"{GRAY}{self.node_debug_str}{RESET}")
                    self.node_debug_str = ""
                    #debug(DEBUG_LEVELS['DEBUG'], "SerialThread", f"Start Byte Found: {byte}")
                    self.packetData.clear()
                    self.packetData.append(byte)
                    self.state = ReceptionState.READ_LENGTH
                    self.network.sess.logging(self.node_debug_str, 2) # sends serial messages to debug
                    self.node_debug_str = ''
                else:
                    # debug_raw(DEBUG_LEVELS['NONE'], chr(byte))
                    self.node_debug_str += chr(byte)
                    if len(self.node_debug_str) > 100:
                        #print(node_debug_str, end="")
                        D.debug_raw(DEBUG_LEVELS['DEVICE'], f"{GRAY}{self.node_debug_str}{RESET}")
                        self.node_debug_str = ""

            elif self.state == ReceptionState.READ_LENGTH:
                self.packetData.append(byte)
                if len(self.packetData) == 3:  # Start byte + 2 length bytes
                    length_high = self.packetData[1]
                    length_low = self.packetData[2]
                    self.packetLength = (length_high << 8) | length_low
                    self.state = ReceptionState.READ_PACKET

            elif self.state == ReceptionState.READ_PACKET:
                self.packetData.append(byte)
                if len(self.packetData) == 3 + self.packetLength:
                    # Process the packet using the external parse_packet function
                    D.debug(DEBUG_LEVELS['DEBUG'], "SerialThread", f"{GRAY}Parsing Incoming: {self.packetData}{RESET}")
                    packet = parse_packet(self.packetData, self.packetLength)
                    if packet is not None:
                        # Packet parsed successfully, return it
                        # Reset state for next packet
                        self.state = ReceptionState.WAIT_FOR_START_BYTE
                        self.packetData.clear()
                        self.packetLength = 0
                        return packet
                    else:
                        # Parsing failed, reset state
                        self.state = ReceptionState.WAIT_FOR_START_BYTE
                        self.packetData.clear()
                        self.packetLength = 0
        return None

@threaded
def serial_thread(network):
    """
    Thread for handling serial communication with nodes.
    
    Args:
        network: NodeNet instance to manage
    """
    receiver = Receiver(network)
    current_time = t.time()
    device_refresh_interval = 5
    
    while not stop_threads_flag.is_set():
        try:
            # Try to receive incoming data
            try: 
                cmd_rec = receiver.receive()
            except s.SerialException:
                D.debug(DEBUG_LEVELS['ERROR'], "Serial", "Serial exception in receiver")
                break
            
            # Process received command if any
            if cmd_rec:
                network.disperse(cmd_rec)
                if hasattr(network, 'sess') and network.sess:
                    network.sess.logging(cmd_rec, 1)
            
            # Process any pending commands to send
            if network.command_buff:
                try:
                    cmd = network.command_buff[0]
                    D.debug(DEBUG_LEVELS['DEBUG'], "SerialThread", f"{GRAY}Sending command to Network {network.idnum}{RESET}")
                    if send_command(cmd, network):
                        if hasattr(network, 'sess') and network.sess:
                            network.sess.logging(cmd, 0)
                        del network.command_buff[0]
                    else:
                        # If send failed, wait a bit before retrying
                        t.sleep(0.1)
                except IndexError:
                    pass  # No commands in buffer
            
            # Periodic device refresh
            if t.time() - current_time >= device_refresh_interval:
                network.refreshDevices()
                current_time = t.time()
            
            # Small sleep to prevent CPU hogging
            t.sleep(0.01)
            
        except Exception as e:
            D.debug(DEBUG_LEVELS['ERROR'], "Serial", f"Error in serial thread: {e}")
            t.sleep(0.1)  # Wait a bit before retrying
    
    stop_threads_flag.clear()  # Clear the flag to signal that the thread has ended

# for th in threadlist:
#         th.join()

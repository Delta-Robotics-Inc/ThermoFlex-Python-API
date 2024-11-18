import sys
import serial as s
import time as t
import struct as st
from .packet import parse_packet, STARTBYTE
from .debug import Debugger as D, DEBUG_LEVELS
import threading as thr
from enum import Enum


stop_threads_flag = thr.Event() # Flag to stop all threads when the thread is ready to close

def threaded(func):
    global threadlist
    threadlist = []
    
    def wrapper(*args, **kwargs):
        thread = thr.Thread(target=func, args=args, kwargs = kwargs)
        thread.start()
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
    print(f'{command_final}\n')
    
    t.sleep(0.05)

def send_command(command, network):
    '''
    
    Sends commands recieved by command_t. Takes command_t object as arguments.
    
    '''
    port = network.arduino
    D.debug(DEBUG_LEVELS['DEBUG'], "send_command", f'Sent Command{command.packet}')
    port.write(bytearray(command.packet))
    t.sleep(0.05)      

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
        #try:
        if port.in_waiting > 0:
            D.debug(DEBUG_LEVELS['DEBUG'], "SerialThread", f"\nReading incoming data from network {self.network.idnum}:")
        elif len(self.node_debug_str) > 0: # If there is no incoming data, but there is debug data, print the debug data
            D.debug_raw(DEBUG_LEVELS['DEVICE'], self.node_debug_str)
            self.node_debug_str = ""
        while port.in_waiting > 0:
            
            # Check if the stop_threads_flag has been set, if so, break the loop and end the thread
            if stop_threads_flag.is_set():
                break

            byte = port.read(1)
            byte = byte[0]  # Convert from bytes to integer

            if self.state == ReceptionState.WAIT_FOR_START_BYTE:
                if byte == STARTBYTE:
                    D.debug(DEBUG_LEVELS['DEVICE'], "SerialThread", self.node_debug_str)
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
                        D.debug_raw(DEBUG_LEVELS['DEVICE'], self.node_debug_str)
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
                    D.debug(DEBUG_LEVELS['DEBUG'], "SerialThread", f"Parsing Incoming: {self.packetData}")
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

    receiver = Receiver(network)

    while True:
        cmd_rec = receiver.receive()

        # Check if the stop_threads_flag has been set, if so, break the loop and end the thread
        if stop_threads_flag.is_set():
            break
        #print(cmd_rec) #DEBUG
        if not cmd_rec:
            pass
        else:
            network.disperse(cmd_rec)
            network.sess.logging(cmd_rec,1)

        try:
            cmd = network.command_buff[0]
            D.debug(DEBUG_LEVELS['DEBUG'], "SerialThread", f"Sending command to Network {network.idnum}")
            #print(cmd.construct) #DEBUG
            send_command(cmd,network)
            network.sess.logging(cmd,0)
            del network.command_buff[0]
        except IndexError:
            #print('No data') #DEBUG
            pass

    stop_threads_flag.clear() # Clear the flag to signal that the thread has ended

        
for th in threadlist:
        th.join()
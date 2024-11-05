import serial as s
import time as t
import struct as st
from .packet import parse_packet, STARTBYTE
import threading as thr
from enum import Enum
#incoming_data = b''

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
    
    print(port)
    print(command.packet)
    print(command_final)
    
    t.sleep(0.05)

def send_command(command, network):
    '''
    
    Sends commands recieved by command_t. Takes command_t object as arguments.
    
    '''
    port = network.arduino
    #print('sent')
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

    def receive(self):
        port = self.network.arduino
        try:
            while port.in_waiting > 0:
                byte = port.read(1)
                byte = byte[0]  # Convert from bytes to integer

                if self.state == ReceptionState.WAIT_FOR_START_BYTE:
                    if byte == STARTBYTE:
                        self.packetData.clear()
                        self.packetData.append(byte)
                        self.state = ReceptionState.READ_LENGTH

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
                        print(f'Parsing: {self.packetData}')
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
        except AttributeError:
            print('ERROR: port not opened... quitting receive thread')
            quit()
        # No packet parsed, return None
        return None


# def receive(network:object): #running check
#     '''
#     id address from network
#     incomoing logging and changes

#     '''
#     start_time = t.time()
#     timeout = 1  # seconds
#     port = network.arduino
#     global incoming_data
#     while True:
#         try:
#             p_iw = port.in_waiting
#             if p_iw > 0:
#                 incoming_data += port.read(p_iw)
#                 print(incoming_data) #DEBUG
#                 # Decode and print received data as characters
                
#             elif t.time() - start_time > timeout:
#                 # No more data, exit loop after timeout
#                 break
#             else:
#                 # No data, wait a bit before checking again
#                 t.sleep(0.01)
#             try:
#                 node_msg = packet_parse(incoming_data)
#                 if not node_msg:
#                     continue
#                 else:
#                     print(incoming_data) #DEBUG
#                     network.disperse(node_msg)
#                     incoming_data = incoming_data[node_msg[2]:]
#                     #print(i_d) #DEBUG
#                     return node_msg
#             except UnboundLocalError:
#                 print("Error: UnboundLocalError")
#                 continue
#         except AttributeError:
#             print('ERROR: port not opened... quitting receive thread') #DEBUG
#             quit()
#             continue
               
#     #TODO: change msg to return full byte string; have network deconstruct packets

@threaded
def serial_thread(network):

    receiver = Receiver(network)

    while True:
        # Check if the stop_threads_flag has been set, if so, break the loop and end the thread
        if stop_threads_flag.is_set():
            break

        cmd_rec = receiver.receive()
        #print(cmd_rec) #DEBUG
        if not cmd_rec:
            pass
        else:
            network.disperse(cmd_rec)
            network.sess.logging(cmd_rec,0)
        
        try:
            cmd = network.command_buff[0]
        except IndexError:
            #print('No data') #DEBUG
            pass
        else:
            #print(cmd.construct) #DEBUG
            send_command(cmd,network)
            network.sess.logging(cmd,1)
            del network.command_buff[0]

    stop_threads_flag.clear() # Clear the flag to signal that the thread has ended
        
for th in threadlist:
        th.join()
import serial as s
import time as t
import struct as st
from .packet import packet_parse
i_d = b''

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
    command_final = b''
    for c in command.packet:
        
        if type(c) == int:
            command_final += st.pack('!B', c)
        elif type(c) == bytes:
            command_final += c
        elif type(c) == str:
            command_final += bytes(c,'ascii')
    
    port.write(command_final)
    t.sleep(0.05)      


def receive(network:object): #running check
    '''
    id address from network
    incomoing logging and changes

    '''
    start_time = t.time()
    timeout = 1  # seconds
    port = network.arduino
    while True:
        p_iw = port.in_waiting
        if p_iw > 0:
            i_d += port.read(port.in_waiting)
            # Decode and print received data as characters
            #print(i_d)
            
        elif t.time() - start_time > timeout:
            # No more data, exit loop after timeout
            break
        else:
            # No data, wait a bit before checking again
            t.sleep(0.1)
        msg = packet_parse(i_d)
        if not msg:
            continue
        else:
            network.disperse(msg)
            i_d = i_d[msg(2):]
            return msg
        
                
    #TODO: change msg to return full byte string; have network deconstruct packets

@threaded
def serialport(network):

    while True:
        cmd_rec = receive(network)
        try:
            cmd = network.command_buff[0]
        except IndexError:
            pass
        else:
            send_command(cmd,network)
            network.sess.logging(cmd,0)
            del network.command_buff[0]

        #send nodeonNet check every 1 minute
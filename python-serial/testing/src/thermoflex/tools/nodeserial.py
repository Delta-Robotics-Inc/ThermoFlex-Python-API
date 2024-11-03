import serial as s
import time as t
import struct as st
from .packet import packet_parse
import threading as thr
i_d = b''

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


def receive(network:object): #running check
    '''
    id address from network
    incomoing logging and changes

    '''
    start_time = t.time()
    timeout = 1  # seconds
    port = network.arduino
    global i_d
    while True:
        try:
            p_iw = port.in_waiting
            if p_iw > 0:
                i_d += port.read(p_iw)
                # Decode and print received data as characters
                
            elif t.time() - start_time > timeout:
                # No more data, exit loop after timeout
                break
            else:
                # No data, wait a bit before checking again
                t.sleep(0.1)
            try:
                msg = packet_parse(i_d)
                #str_msg = pack_parse(i_d.decode('utf-8'))
                if not msg:
                    continue
                else:
                    #print(i_d)
                    network.disperse(msg)
                    i_d = i_d[msg[2]:]
                    #print(i_d)
                    return msg
            except UnboundLocalError:
                continue
        except AttributeError:
            #print('port not opened')
            continue
               
    #TODO: change msg to return full byte string; have network deconstruct packets

@threaded
def serialport(network):

    while True:
        cmd_rec = receive(network)
        #print(cmd_rec)
        if not cmd_rec:
            pass
        else:
            network.sess.logging(cmd_rec,0)
        
        try:
            cmd = network.command_buff[0]
        except IndexError:
            #print('No data')
            pass
        else:
            #print(cmd.construct)
            send_command(cmd,network)
            network.sess.logging(cmd,1)
            del network.command_buff[0]
        
    #send nodeonNet check every 1 minute
for th in threadlist:
        th.join()
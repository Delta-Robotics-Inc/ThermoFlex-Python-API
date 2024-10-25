import serial as s
import time as t
import struct as st

def send_command_str(command, port): #TODO: construct packet in commmand, remove send_command options
    '''
    
    Prints the command to a terminal. Used for test purposes.
    
    '''
     
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

def send_command(command, port):
    '''
    
    Sends commands recieved by command_t. Takes command_t object as arguments.
    
    '''
    command_final = b''
    for c in command.packet:
        if type(c) == str:
            command_final += bytes(c,'ascii')
        elif type(c) == int:
            command_final += st.pack('!B', c)
        elif type(c) == bytes:
            command_final += c
    
    port.write(command_final)
    t.sleep(0.05)      


def receive(network:object):
    '''
    id address from network
    incomoing logging and changes

    '''
    start_time = t.time()
    timeout = 1  # seconds
    port = network.arduino
    msg = None
    i_d = b''
    while True:
        p_iw = port.in_waiting
        if p_iw > 0:
            i_d += port.read(port.in_waiting)
            # Decode and print received data as characters
            #print(i_d)
            for b in i_d: 
                if b == 126:                    
                    try:
                        z = i_d.index(b)
                        l = i_d[z+1:z+3]
                        n = ''
                        for y in l:
                            n += str(y)
                        if int(n)+3 > p_iw:
                            break
                    except IndexError:
                        break
                    finally:                                               
                        n = int(n)-10
                        try:
                            msg = (i_d[z+6:z+9],i_d[z+12:z+12+n])
                            i_d = i_d[z+13+n:]
                        except UnicodeDecodeError:
                                print("[Error decoding data]")
        elif t.time() - start_time > timeout:
            # No more data, exit loop after timeout
            break
        else:
            # No data, wait a bit before checking again
            t.sleep(0.1)

        try:
            if len(msg)>0:
                break
        except UnboundLocalError:
            pass
                
    #TODO: change msg to return full byte string; have network deconstruct packets
    return msg
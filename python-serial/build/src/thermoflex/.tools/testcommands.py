import time as t
import random as r
from thermoflex.commands import node, muscle, command_t


def random_number(length):
    start = 10**(length-1)
    end = (10**length) - 1
    return r.randint(start, end)


    
    
class testnode(node):
    def __init__(self):
        super().init()
        self.port0 = 'COMT'
        self.serial = random_number(12)
    
    def send_command_str(self, command): #construct string then send
        '''
        
        Prints the command sent.
        
        '''
        command_str = None
        port = self.arduino
        command_str = f"{command.name} {command.device}"
        if command.code == 0xFF or command.code == 0x04:
            command_str = command_str
            
        elif command.code == 0xFE:
            pass
        else:    
            
            for p in command.params:
                command_str = command_str + str(p).lower() # Current string implementation
                 
        print(command_str)
        
        t.sleep(0.05)
        
    def send_command(self, command):
        '''
        
        Prints the command sent.
        
        '''    
        command_str = None
        port = self.arduino
        command_str = f"{command.name} {command.device}"
        if command.code == 0xFF or command.code == 0x04:
            command_str = command_str
            
        elif command.code == 0xFE:
            pass
        else:    
            
            for p in command.params:
                command_str = command_str + str(p).lower() # Current string implementation
                 
        print(command_str)
        
        t.sleep(0.05)
#override node classes
import time as t
import random as r
from thermoflex.commands import *


def random_number(length):
    start = 10**(length-1)
    end = (10**length) - 1
    return r.randint(start, end)


class testnet(nodenet):
    def __init__(self):
        self.id = 0xFF
        self.port = 'PortT'
        
    def send_packet(self,node,cmd):
        send_command_str(node, cmd, self.arduino)
    
    def receive_packet(self):
        print('goes to receive func')

class testnode(node):
    def __init__(self):
        super().init()
        self.serial = random_number(12)
    
    
#override node classes
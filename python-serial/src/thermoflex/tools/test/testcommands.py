import time as t
import random as r
from thermoflex.network import *
from thermoflex.devices import *
from ..nodeserial import Receiver, send_command_str



def random_number(length):
    start = 10**(length-1)
    end = (10**length) - 1
    return r.randint(start, end)


class testnet(NodeNet):
    def __init__(self):
        self.idnum = 0x54
        self.port = 'PortT'

class testnode(Node):
    def __init__(self):
        super().init()
        self.serial = random_number(3)
        
#override node classes
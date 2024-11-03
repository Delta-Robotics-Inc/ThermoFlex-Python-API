from . import tfnode_messages_pb2 as tfproto
STARTBYTE = 0x7E
PROTOVER = 0x01
SENDID = [0x00,0x00,0x00]
IDTYPE = 0x00
CHECKSUM = 0xFF
PROTOSIZE = 1
IDTYPESIZE = 1
IDSIZE = 3
CHECKSUM = 1

# [Start Byte][Packet Length][Protocol Version][Sender ID Type][Destination ID Type][Sender ID][Destination ID][Data][Checksum]

def packet_size(data:str):
    '''
    Takes data string, returns 2 element tuple of 4 digit byte data length in integer
    EX.[(01,75)]

    '''
    statics = PROTOSIZE + IDSIZE + IDSIZE + IDTYPESIZE + IDTYPESIZE + CHECKSUM
    datasize = len(data)
    length = statics + datasize
    length = f'{length}'
    while len(length)<4:
        length = '0'+length
    length = (int(length[:2]),int(length[2:]))

    return length

def checksum_cal(dest_id, data):
    # Calculate checksum
    checksum = 0
    checksum ^= PROTOVER
    checksum ^= IDTYPE
    checksum ^= IDTYPE
    for byte in SENDID:
        checksum ^= byte
    for byte in dest_id:
        checksum ^= byte
    for byte in data:
        checksum ^= byte
    return checksum


def packet_parse(inc:str):
    for b in inc: 
        if b == 126:                    
            try:
                z = inc.index(b)
                l = inc[z+1:z+3]
                n = ''
                for y in l:
                    n += str(y)
                if int(n)+3 > len(inc):
                    break 
            except IndexError:
                break
            finally:                                               
                n = int(n)-10
                q = []
                for x in inc[z+6:z+9]:
                    q.append(x)                   
                try:
                    msg = (q,inc[z+12:z+12+n], n+z+13)
                except UnicodeDecodeError:
                    print("[Error decoding data]")
                #print(msg)   #DEBUG
                return msg
    return

def deconstructor(data):
    read_data = ''
    data = tfproto.NodeResponse.FromString(data)
    
    if data.HasField('general_response'):
        read_data += 'general'
        #print('general')    #DEBUG
        if data.general_response.Hasfield('device'): read_data += f' dev:{data.general_response.device}'
        if data.general_response.Hasfield('received_cmd'): read_data += f' rec_cmd:{data.general_response.received_cmd}'
        if data.general_response.Hasfield('response_code'): read_data += f' code:{data.general_response.response_code}'
        #print(read_data)   #DEBUG     
    elif data.HasField('status_response'):
        read_data += 'status'
        print('status')   #DEBUG  
        data = data.status_response
        
        if data.HasField('device'): read_data += f' dev:{data.status_response.device}'

        if data.HasField('node_status_compact'): 
            #read_data += f' CompactStatus:{data.node_status_compact}'
            read_data += f' Compact_values uptime:{data.node_status_compact.uptime}'
            read_data += f' errors:{data.node_status_compact.error_code} volt_supply:{data.node_status_compact.v_supply}'
            read_data += f' pot_values:{data.node_status_compact.pot_val}' 
        
        elif data.HasField('node_status_dump'): 
            #read_data += f' compact:{data.node_status_dump}'
            read_data += f' Compact_values uptime:{data.node_status_dump.compact_status.uptime}'
            read_data += f' errors:{data.node_status_dump.compact_status.error_code}'
            read_data += f' volt_supply:{data.node_status_dump.compact_status.v_supply}'
            read_data += f' pot_values:{data.node_status_dump.compact_status.pot_val}' 
            read_data += f' Settings can_id:{data.node_status_dump.loaded_settings.can_id}.{data.node_status_dump.firmware_subversion}'
            read_data += f' Dump_values firmware:{data.node_status_dump.firmware_version}'
            read_data += f' board_ver:{data.node_status_dump.board_version}.{data.node_status_dump.board_subversion}'
            read_data += f' muscle_count:{data.node_status_dump.muscle_cnt}'
            read_data += f' log_interval:{data.node_status_dump.log_interval_ms}'
            read_data += f' vrd_scalar:{data.node_status_dump.vrd_scalar}'
            read_data += f' vrd_offset:{data.node_status_dump.vrd_offset}'
            read_data += f' max_current:{data.node_status_dump.max_current}'
            read_data += f' min_v_supply:{data.node_status_dump.min_v_supply}'
             

        elif data.HasField('sma_status_compact'): 
            #read_data += f' Compact:{data.sma_status_compact}'
            read_data += f' Compact dev:{data.sma_status_compact.device_port}'
            read_data += f' enable_status:{data.sma_status_compact.enabled}'
            read_data += f' control_mode:{data.sma_status_compact.mode}'
            read_data += f' pwm_out:{data.sma_status_compact.output_pwm}'
            read_data += f' load_amps:{data.sma_status_compact.load_amps}'
            read_data += f' laod_voltdrop:{data.sma_status_compact.load_vdrop}'
            read_data += f' load_ohms:{data.sma_status_compact.load_mohms}' 
        
        elif data.HasField('sma_status_dump'): 
            #read_data += f' Dump:{data.sma_status_dump}' 
            read_data += f' Compact_values dev:{data.sma_status_dump.compact_status.device_port}'
            read_data += f' enable_status:{data.sma_status_dump.compact_status.enabled}'
            read_data += f' control_mode:{data.sma_status_dump.compact_status.mode}'
            read_data += f' pwm_out:{data.sma_status_dump.compact_status.output_pwm}'
            read_data += f' load_amps:{data.sma_status_dump.compact_status.load_amps}'
            read_data += f' laod_voltdrop:{data.sma_status_dump.compact_status.load_vdrop}'
            read_data += f' load_ohms:{data.sma_status_dump.compact_status.load_mohms}' 
            read_data += f' SMA_Settings default_mode:{data.sma_status_dump.loaded_settings.default_mode}'
            read_data += f' deafult_setpoint:{data.sma_status_dump.loaded_settings.default_setpoint}'
            read_data += f' rcontrol_kp:{data.sma_status_dump.loaded_settings.rcntrl_kp}'
            read_data += f' rcontrol_ki:{data.sma_status_dump.loaded_settings.rcntrl_ki}'
            read_data += f' rcontrol_kd:{data.sma_status_dump.loaded_settings.rcntrl_kd}'
            read_data += f' Dump_values vld_scalar:{data.sma_status_dump.vld_scalar}'
            read_data += f' vld_offset:{data.sma_status_dump.vld_offset}'
            read_data += f' r_sns_ohms:{data.sma_status_dump.r_sns_ohms}'
            read_data += f' amp_gain:{data.sma_status_dump.amp_gain}'
            read_data += f' af_mohms:{data.sma_status_dump.af_mohms}'
            read_data += f' delta_mohms:{data.sma_status_dump.delta_mohms}'
            read_data += f' trainstate:{data.sma_status_dump.trainState}'
    else:
        pass
    print(read_data)   #DEBUG
    return read_data
        
#---------------------------------------------------------------------------------------

class command_t:
    
    '''
    
    Class dedicated to holding and sending the command codes.
    
    '''
    commanddefs = {"set-enable": [0x01, [bool]], #state
			       "set-mode": [0x02, [int]], #mode
			       "set-setpoint": [0x03, [int, float]], #mode, value
			       "status": [0x04, [int]], #Update to match node firmware  
                   "log-mode": [0x05, [int]], #log mode(subject to change)
			       "configure": [0x06,[int,int]],
                   "silence":[0x07,[bool]],
                   "reset": [0xFF, []]
			       } 
    devicedef = ("all", "node","portall", "m1", "m2")
	
    modedef = ("percent" , "amps", "volts", "ohms", "train")
    
    def __init__(self, node:object, name:str, params:list, device = 'node' ):
    	#valid command checking
        self.params = params 
        self.device = device
        try:
            self.devcode = command_t.devicedef.index(self.device)
        except:
            raise KeyError("Incorrect device")
        self.name = name
        try:
            self.code = command_t.commanddefs[name][0]
        except:
            self.code = 0x00  # Invalid code reserved for 0
            raise KeyError("Invalid command name")     
                       
        if self.isValid(command = self.name, params = self.params) is True:
            pass
        elif self.isValid(command = self.name, params = self.params) is False:
            raise ValueError("Incorrect arguments for this command") 
        #packet construction
        self.destnode = node
        self.construct = self.sConstruct()
        self.length = packet_size(self.construct)
        self.type = IDTYPE
        self.packet = self.packet_construction()
        #print(tfproto.NodeCommand.FromString(self.construct))
           
    def getName(code:hex):
       for x in command_t.commanddefs:
           if code == command_t.commanddefs[x][0]:
               return x

    def isValid(self, command, params:list):
       ''' 
           
       Check if name, code, and params match one of the definitions.
           
       '''
       z = 0 
       for x in params:
           if type(x) == self.commanddefs[command][1][z]:
               z+=1
               continue
           else:
               return False
       return True
    
    def get_device_code(self): # tfproto.Device
        """
          Returns the device code based on the device code index.
        """

        if self.devcode == 0:
            device_code = tfproto.Device.DEVICE_ALL
        elif self.devcode == 1:
            device_code = tfproto.Device.DEVICE_NODE
        elif self.devcode == 2:
            device_code = tfproto.Device.DEVICE_PORTALL
        elif self.devcode == 3:
            device_code = tfproto.Device.DEVICE_PORT1
        elif self.devcode == 4:
            device_code = tfproto.Device.DEVICE_PORT2

        return device_code           
        
    def set_mode(self):# tfproto.SMAControlMode
        
        if self.params[0] == 0:
            mode = tfproto.SMAControlMode.MODE_PERCENT
        elif self.params[0] == 1:
            mode = tfproto.SMAControlMode.MODE_AMPS
        elif self.params[0] == 2 :
            mode = tfproto.SMAControlMode.MODE_VOLTS
        elif self.params[0] == 3:
            mode = tfproto.SMAControlMode.MODE_OHMS
        elif self.params[0] == 4:
            mode = tfproto.SMAControlMode.MODE_TRAIN
           
        return mode
    
    def statusenum(self): # tfproto.DeviceStatusMode
        x = None
        if self.params[0] == 0:
            x = tfproto.DeviceStatusMode.STATUS_NONE
        elif self.params[0]== 1:
            x = tfproto.DeviceStatusMode.STATUS_COMPACT
        elif self.params[0] == 2:
            x = tfproto.DeviceStatusMode.STATUS_DUMP
        elif self.params[0] == 3:
            x = tfproto.DeviceStatusMode.STATUS_DUMP_READABLE
        return x
    
    def sConstruct(self):
        '''
        Constructs the .proto command from command_t object. Returns bytes string.
        '''
        node_cmd = tfproto.NodeCommand()
        if self.code == 0x01:
            if self.params[0] == True:
                node_cmd.enable.device = self.get_device_code()
            elif self.params[0] == False:
                node_cmd.disable.device = self.get_device_code()
         # ask Mark about .proto format- class structure
        elif self.code == 0x02:
            node_cmd.set_mode.device = self.get_device_code()
            node_cmd.set_mode.mode = self.set_mode()
        elif self.code == 0x03:
            node_cmd.set_setpoint.device = self.get_device_code()            
            node_cmd.set_setpoint.mode = self.set_mode()
            node_cmd.set_setpoint.setpoint = self.params[1]
        elif self.code == 0x04:
            node_cmd.status.device = self.get_device_code()
            node_cmd.status.mode = self.statusenum()
            node_cmd.status.repeating = False
        elif self.code == 0x05:
            node_cmd.status.device = self.get_device_code()
            node_cmd.status.mode = self.statusenum()
            node_cmd.status.repeating = True
        elif self.code == 0x06:
            node_cmd.configure_settings.device = self.get_device_code()
            node_cmd.configure_settings.can_id = self.params[0]
        elif self.code == 0x07:
            node_cmd.silence_node.silence = self.params[0]
        elif self.code == 0xFF:
            node_cmd.reset.device = self.get_device_code()
        #print(node_cmd.SerializeToString())
        return node_cmd.SerializeToString()

    def packet_construction(self):
        
        
        packet = [PROTOVER,IDTYPE,IDTYPE]
        plength = packet_size(self.construct)
        packet.insert(0,plength[1])
        packet.insert(0,plength[0])
        packet.insert(0,STARTBYTE)
        packet.extend(SENDID)
        packet.extend(self.destnode.addr)
        packet.extend(self.construct)
        packet.append(checksum_cal(self.destnode.addr,self.construct))
        p = []
        
        
        #construct packet in bytes
        for x in packet:
            if type(x) == str:
                p.append(x)
            elif type(x) == int:
                p.append(x)
    
        return p
    
    
         
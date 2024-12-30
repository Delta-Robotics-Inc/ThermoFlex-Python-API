from . import tfnode_messages_pb2 as tfproto
from .debug import Debugger as D, DEBUG_LEVELS
from enum import Enum

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
class DATATYPE(Enum):
    SENT = 0
    RECEIVE = 1
    ERROR = 2
    WARNING = 3
    DEBUG = 4


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

def checksum_cal(protocol_version, sender_id_type, destination_id_type, sender_id, dest_id, data):
    # Calculate checksum
    checksum = 0
    checksum ^= protocol_version
    checksum ^= sender_id_type
    checksum ^= destination_id_type
    for byte in sender_id:
        checksum ^= byte
    for byte in dest_id:
        checksum ^= byte
    for byte in data:
        checksum ^= byte
    return checksum

def parse_packet(data, packet_length):
    # data is a bytearray containing the entire packet
    # Extract fields based on your protocol
    try:
        # Validate start byte
        if data[0] != STARTBYTE:
            return None
        # Verify packet length
        if len(data) != 3 + packet_length:
            D.debug(DEBUG_LEVELS['INFO'], "parse_packet", "Incorrect packet length, returning")
            return None

        # Extract protocol version
        protocol_version = int(data[3])
        # Extract sender ID type and destination ID type
        sender_id_type = int(data[4])
        destination_id_type = int(data[5])
        # Extract sender ID and destination ID
        sender_id = list(data[6:9])
        destination_id = list(data[9:12])
        # Extract data payload
        payload = data[12:-1]
        # Extract checksum
        received_checksum = int(data[-1])

        # Calculate checksum with values
        calculated_checksum = checksum_cal(
            protocol_version,
            sender_id_type,
            destination_id_type,
            sender_id,
            destination_id,
            payload
        )
        if calculated_checksum != received_checksum:
            D.debug(DEBUG_LEVELS['INFO'], "parse_packet", "Checksum mismatch, returning")
            return None
        
        # Create a packet dictionary
        packet = {
            'protocol_version': protocol_version,
            'sender_id_type': sender_id_type,
            'destination_id_type': destination_id_type,
            'sender_id': sender_id,
            'destination_id': destination_id,
            'payload': payload
        }
        return packet
    except Exception as e:
        D.debug(DEBUG_LEVELS['ERROR'], "parse_packet", f"Error parsing packet: {e}")
        return None

def deconst_serial_response(data):
    response_type = ''
    response_dict = {}
    data = tfproto.NodeResponse.FromString(data)
    #print(data)       #DEBUG
    read_data = "none"
    
    if data.HasField('general_response'):
        read_data = 'general'
        #print('general')    #DEBUG
        response_dict['dev'] = data.general_response.device
        response_dict['rec_cmd'] = data.general_response.received_cmd
        response_dict['code'] = data.general_response.response_code
        #print(read_data)   #DEBUG     
    elif data.HasField('status_response'):
        read_data = 'status'
        #print('status')   #DEBUG  
        data = data.status_response
        
        response_dict['Status_dev'] = data.device

        if data.HasField('node_status_compact'): 
            read_data += ' node compact'
            #response_dict['CompactStatus'] = data.node_status_compact
            response_dict['uptime'] = data.node_status_compact.uptime
            response_dict['errors'] = data.node_status_compact.error_code 
            response_dict['volt_supply'] = data.node_status_compact.v_supply
            response_dict['pot_values'] = data.node_status_compact.pot_val
        
        elif data.HasField('node_status_dump'): 
            read_data += ' node dump'
            #response_dict['compact'] = data.node_status_dump
            response_dict['uptime'] = data.node_status_dump.compact_status.uptime
            response_dict['errors'] = data.node_status_dump.compact_status.error_code
            response_dict['volt_supply'] = data.node_status_dump.compact_status.v_supply
            response_dict['pot_values'] = data.node_status_dump.compact_status.pot_val 
            response_dict['can_id'] = f'{data.node_status_dump.loaded_settings.can_id}'
            response_dict['firmware'] = f'{data.node_status_dump.firmware_version}.{data.node_status_dump.firmware_subversion}'
            response_dict['board_ver'] = f'{data.node_status_dump.board_version}.{data.node_status_dump.board_subversion}'
            response_dict['muscle_count'] = data.node_status_dump.muscle_cnt
            response_dict['log_interval'] = data.node_status_dump.log_interval_ms
            response_dict['vrd_scalar'] = data.node_status_dump.vrd_scalar
            response_dict['vrd_offset'] = data.node_status_dump.vrd_offset
            response_dict['max_current'] = data.node_status_dump.max_current
            response_dict['min_v_supply'] = data.node_status_dump.min_v_supply
             

        elif data.HasField('sma_status_compact'): 
            read_data += f' SMA compact {data.sma_status_compact.device_port}'
            #response_dict['Compact'] = data.sma_status_compact
            response_dict['dev'] = data.sma_status_compact.device_port
            response_dict['enable_status'] = data.sma_status_compact.enabled
            response_dict['control_mode'] = data.sma_status_compact.mode
            response_dict['pwm_out'] = data.sma_status_compact.output_pwm
            response_dict['load_amps'] = data.sma_status_compact.load_amps
            response_dict['load_voltdrop'] = data.sma_status_compact.load_vdrop
            response_dict['load_ohms'] = data.sma_status_compact.load_mohms 
        
        elif data.HasField('sma_status_dump'): 
            read_data += f' SMA dump {data.sma_status_compact.device_port}'
            #response_dict['Dump'] = data.sma_status_dump 
            response_dict['dev'] = data.sma_status_dump.compact_status.device_port
            response_dict['enable_status'] = data.sma_status_dump.compact_status.enabled
            response_dict['control_mode'] = data.sma_status_dump.compact_status.mode
            response_dict['pwm_out'] = data.sma_status_dump.compact_status.output_pwm
            response_dict['load_amps'] = data.sma_status_dump.compact_status.load_amps
            response_dict['load_voltdrop'] = data.sma_status_dump.compact_status.load_vdrop
            response_dict['load_ohms'] = data.sma_status_dump.compact_status.load_mohms 
            response_dict['SMA_default_mode'] = data.sma_status_dump.loaded_settings.default_mode
            response_dict['SMA_default_setpoint'] = data.sma_status_dump.loaded_settings.default_setpoint
            response_dict['SMA_rcontrol_kp'] = data.sma_status_dump.loaded_settings.rcntrl_kp
            response_dict['SMA_rcontrol_ki'] = data.sma_status_dump.loaded_settings.rcntrl_ki
            response_dict['SMA_rcontrol_kd'] = data.sma_status_dump.loaded_settings.rcntrl_kd
            response_dict['vld_scalar'] = data.sma_status_dump.vld_scalar
            response_dict['vld_offset'] = data.sma_status_dump.vld_offset
            response_dict['r_sns_ohms'] = data.sma_status_dump.r_sns_ohms
            response_dict['amp_gain'] = data.sma_status_dump.amp_gain
            response_dict['af_mohms'] = data.sma_status_dump.af_mohms
            response_dict['delta_mohms'] = data.sma_status_dump.delta_mohms
            response_dict['trainstate'] = data.sma_status_dump.trainState

    else:
        pass
    D.debug(DEBUG_LEVELS['DEBUG'], "deconst_response_packet", f"Response Type: {read_data}")
    D.debug(DEBUG_LEVELS['DEBUG'], "deconst_response_packet", f"Response Packet Data: {response_dict}")
    return (read_data, response_dict)
        
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
	
    modedef = ("percent" , "amps", "volts", "ohms", "train", "count")
    
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
        packet.extend(self.destnode.node_id)
        packet.extend(self.construct)

        # Construct packet with constants and node info
        packet.append(checksum_cal(PROTOVER, IDTYPE, IDTYPE, SENDID, self.destnode.node_id, self.construct))
        p = []
        
        #construct packet in bytes
        for x in packet:
            if type(x) == str:
                p.append(x)
            elif type(x) == int:
                p.append(x)
    
        return p
#-----------------------------------------------------------------------------------------
class LogMessage: #object for log messages
    
    def __init__(self, msg_type, gen_msg):
        self.message_type = msg_type
        self.message_address = 0
        self.generated_message = gen_msg
        
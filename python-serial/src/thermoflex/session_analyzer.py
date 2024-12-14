import re
import pandas as pd
from .tools import tfnode_messages_pb2 as tfproto
from .tools.packet import deconst_serial_response

class SessionAnalyzer:
    def __init__(self):
        """
        Initialize the SessionAnalyzer with a given session file.
        :param session_file: Path to the session file.
        """
        self.logs = []
    
    def load_session(self, session_file):
        """
        Load and parse the session file into log lines.
        """
        self.session_file = session_file
        with open(session_file, 'r') as file:
            self.logs = file.readlines()

    def parse_node_id(self, device_str):
        """
        Parse the node ID from either `[1, 2, 3]` format or its integer representation.
        :param device_str: Node ID as a string (e.g., "[1, 2, 3]" or "66051").
        :return: Tuple (byte_list, integer_id).
        """
        if device_str.startswith('['):  # Handle "[1, 2, 3]" format
            byte_list = [int(x.strip()) for x in device_str.strip('[]').split(',')]
            integer_id = int.from_bytes(byte_list, byteorder='big')
        else:  # Handle "66051" format
            integer_id = int(device_str)
            # Convert integer to byte list (3 bytes for the example)
            byte_list = list(integer_id.to_bytes(3, byteorder='big'))
        return byte_list, integer_id

    def extract_to_csv(self, output_csv):
        """
        Extract relevant sensor data logs and save them to a CSV file.
        :param output_csv: Path to the output CSV file.
        """
        # Define all possible columns.  Make sure to keep this in sync with packet.deconst_serial_response()
        all_columns = [
            "DATETIME", "DEVICE ID", "STATUS TYPE", 
            "uptime", "errors", "volt_supply", "pot_values",
            "can_id", "firmware", "board_ver", "muscle_count",
            "log_interval", "vrd_scalar", "vrd_offset", "max_current",
            "min_v_supply", "enable_status", "control_mode", "pwm_out",
            "load_amps", "load_voltdrop", "load_ohms", "SMA_default_mode",
            "SMA_default_setpoint", "SMA_rcontrol_kp", "SMA_rcontrol_ki",
            "SMA_rcontrol_kd", "vld_scalar", "vld_offset", "r_sns_ohms",
            "amp_gain", "af_mohms", "delta_mohms", "trainstate"
        ]

        # Initialize an empty DataFrame with all possible columns
        df = pd.DataFrame(columns=all_columns)

        # Regex for matching relevant log lines
        log_regex = r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\.\d{3}) RECEIVED (\[.*?\]|\d+) bytearray\((.+)\)'

        for line in self.logs:
            match = re.match(log_regex, line)
            if match:
                datetime, device, data = match.groups()

                print(f"Datetime: {datetime}")
                print(f"Device ID: {device}")
                print(f"Bytearray Data: {data}\n")

                # Parse node ID (handles both formats) -> Choose one
                dev_byte_list, dev_integer_id = self.parse_node_id(device)

                # Convert data to actual bytearray and parse
                byte_data = eval(f'bytearray({data})')
                response_type, response_dict = deconst_serial_response(byte_data)

                # Skip general responses
                if response_type == "general":
                    continue

                # Add common fields
                row = {
                    "DATETIME": datetime,
                    "DEVICE ID": dev_integer_id,
                    "STATUS TYPE": response_type,
                }

                # Add all parsed fields
                row.update({key: response_dict.get(key, '') for key in all_columns if key not in row})

                # Append to the DataFrame
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

        # Save DataFrame to CSV
        df.to_csv(output_csv, index=False)
        print(f"Extracted data saved to {output_csv}")

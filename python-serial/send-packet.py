import serial
import sys
import time

def construct_packet(destination_id, sender_id=[0xAA, 0xBB, 0xCC], data=b''):
    """
    Constructs a packet according to the specified packet structure.
    Parameters:
        destination_id (list of int): The destination node ID (3 bytes).
        sender_id (list of int): The sender node ID (3 bytes), default is [0xAA, 0xBB, 0xCC].
        data (bytes): The data payload (optional), default is empty.
    Returns:
        list of int: The constructed packet as a list of bytes.
    """
    startByte = 0x7E
    protocolVersion = 0x01
    senderIdType = 0x00  # NodeID
    destinationIdType = 0x00  # NodeID

    rawData = []
    rawData.append(startByte)
    rawData.extend([0x00, 0x00])  # Placeholder for packetLength
    rawData.append(protocolVersion)
    rawData.append(senderIdType)
    rawData.append(destinationIdType)
    rawData.extend(sender_id)
    rawData.extend(destination_id)
    rawData.extend(data)

    # Calculate packet length (excluding Start Byte and Packet Length fields), including checksum
    length = len(rawData) - 3 + 1  # Add 1 for the checksum

    # Set packet length fields
    rawData[1] = (length >> 8) & 0xFF  # High byte
    rawData[2] = length & 0xFF         # Low byte

    # Calculate checksum
    checksum = 0
    checksum ^= protocolVersion
    checksum ^= senderIdType
    checksum ^= destinationIdType
    for byte in sender_id:
        checksum ^= byte
    for byte in destination_id:
        checksum ^= byte
    for byte in data:
        checksum ^= byte

    rawData.append(checksum)

    return rawData


def main():
    '''if len(sys.argv) < 2:
        print("Usage: python send_and_receive_packets.py <serial_port>")
        sys.exit(1)

    serial_port = sys.argv[1]'''
    serial_port = "COM5"
    baudrate = 115200  # Adjust to match your device's baud rate

    # Open the serial port
    try:
        ser = serial.Serial(serial_port, baudrate, timeout=1)
        print(f"Opened serial port {serial_port} at {baudrate} baud.")
    except serial.SerialException as e:
        print(f"Failed to open serial port {serial_port}: {e}")
        sys.exit(1)

    # Flush any existing input
    ser.flushInput()

    # Construct Packet 1 (addressed to node 0x01 0x02 0x03)
    packet1 = construct_packet(destination_id=[0x01, 0x02, 0x03])

    # Construct Packet 2 (addressed to a different node 0x04 0x05 0x06)
    packet2 = construct_packet(destination_id=[0x04, 0x05, 0x06])

    # Send Packet 1
    print("\nSending Packet 1:")
    print(' '.join('{:02X}'.format(b) for b in packet1))
    ser.write(bytearray(packet1))
    ser.flush()

    # Wait for response
    time.sleep(0.5)  # Adjust as needed

    # Read and print incoming messages
    print("\nIncoming messages after Packet 1:")
    read_and_print_messages(ser)

    # Send Packet 2
    print("\nSending Packet 2:")
    print(' '.join('{:02X}'.format(b) for b in packet2))
    ser.write(bytearray(packet2))
    ser.flush()

    # Wait for response
    time.sleep(0.5)  # Adjust as needed

    # Read and print incoming messages
    print("\nIncoming messages after Packet 2:")
    read_and_print_messages(ser)

    # Close the serial port
    ser.close()
    print("\nPackets sent and responses received successfully.")

def read_and_print_messages(ser):
    """
    Reads incoming messages from the serial port and prints them as characters.
    """
    start_time = time.time()
    timeout = 2  # seconds

    while True:
        if ser.in_waiting > 0:
            incoming_data = ser.read(ser.in_waiting)
            # Decode and print received data as characters
            try:
                decoded_data = incoming_data.decode('utf-8', errors='replace')
                print(decoded_data, end='')
            except UnicodeDecodeError:
                print("[Error decoding data]")
        elif time.time() - start_time > timeout:
            # No more data, exit loop after timeout
            break
        else:
            # No data, wait a bit before checking again
            time.sleep(0.1)


if __name__ == '__main__':
    main()

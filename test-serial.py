import serial
ser = serial.Serial('/dev/ttyS2', 115200, timeout=1)
print("Port opened:", ser.name)
ser.close()

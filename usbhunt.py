import serial  # imports pyserial
import serial.tools.list_ports as list_ports

# List all comports
all_ports = list_ports.comports()
#print(all_ports)

# Each entry in the `all_ports` list is a serial device. Check it's
# description and device attributes to learn more
#first_serial_device = all_ports[0]
#print(len(all_ports))
i=0
while i < len(all_ports):
    serial_device = all_ports[i]
    print(serial_device.device,serial_device.description)
    i +=1

i=0
while i < len(all_ports):
    serial_device = all_ports[i]
    if 'Board' in str(serial_device.description):
        #print(serial_device.device,serial_device.description)
        print("hand box is on:           ",serial_device.device)
    elif 'GPS' in str(serial_device.description):
        print("GPS module is on:         ",serial_device.device)
    elif 'Serial' in str(serial_device.description):
        print("USB-Serial adapter is on: ",serial_device.device)
    else:
        print("Camera is on:             ",serial_device.device)
    i +=1

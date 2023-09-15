
import serial
import time

serServoCat = serial.Serial("/dev/ttyUSB0",
                baudrate=9600,
                stopbits=1,
                bytesize=8,
                writeTimeout=0,
                timeout=0,
                rtscts=False,
                dsrdtr=False,
                )

txtGo = "g12.345 +12.345"
txtStop = "g99.999 099.999"

def checkSum(txt):
    xor = 0
    i = 1
    while i < len(txt):
        xor = xor ^ ord(txt[i])
        i += 1    
    print('sending ',txt, 'checksum',hex(xor))
    txt = txt + chr(xor)
    return(txt)

txt = checkSum(txtGo)
serServoCat.write(bytes(txt.encode('ascii)')))

time.sleep(3)
txt = checkSum(txtStop)
serServoCat.write(bytes(txt.encode('ascii)')))

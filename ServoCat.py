import serial
import time


class ServoCat:
    """The ServoCat utility class"""

    def __init__(self) -> None:
        """Initializes the ServoCat link
        Parameters: None
        """
        try:
            self.ser = serial.Serial("/dev/ttyUSB0", baudrate=9600)
            print('ServoCat USB opened')   
        except:
            print("no USB to ServoCat found")
            pass

    def send(self, txt: str) -> None:
        """Write a message to the ServoCat

        Parameters:
        txt (str): The text to send to the Nexus DSC
        """
        xor = 0
        i = 0
        while i < len(txt):
            xor = xor ^ ord(txt[i])
            i += 1    
        txt = txt + chr(xor)
        print('sending ',txt)
        self.ser.write(bytes(txt.encode('ascii')))
        

    
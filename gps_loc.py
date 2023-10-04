#import serial
#import time
#import socket
from skyfield.api import wgs84
#from datetime import datetime, timedelta
import os
#import math
#import re
import Display
import Coordinates
from gps3 import agps3


class GPSread:
    """The GPSread utility class"""

    def __init__(self, handpad: Display, coordinates: Coordinates) -> None:
        """Initializes

        Parameters:
        handpad (Display): The handpad that is connected to the eFinder
        coordinates (Coordinates): The coordinates utility class to be used in the eFinder
        """
        self.handpad = handpad
        self.aligned = False
        self.gps_link = "none"
        self.coordinates = coordinates
        self.gps_Str = "not connected"
        self.long = 0
        self.lat = 0
        self.alt = 0
        

    def read(self) -> None:
        """Establishes that Nexus DSC is talking to us and get observer location and time data"""
        count = 0
        gps_socket = agps3.GPSDSocket()
        data_stream = agps3.DataStream()
        try:
            gps_socket.connect()
            gps_socket.watch()
            for new_data in gps_socket:
                if new_data:
                    print(new_data)
                    data_stream.unpack(new_data)
                    if data_stream.mode == 3:
                        print('Geo data:',data_stream.time, data_stream.lon,data_stream.lat,data_stream.alt)
                        self.date = data_stream.time
                        self.lat = data_stream.lat
                        self.long = data_stream.lon
                        self.alt = data_stream.alt
                        break
                    elif data_stream.mode == 0:
                        print('no lock yet')
                        count +=1
                        if count > 10:
                            print('giving up')
                            gps_socket.close()
                            break
        except:
            print ('No gps dongle found')
            exit()

        self.location = self.coordinates.get_earth() + wgs84.latlon(self.lat, self.long)
        #print("gps UTC", self.date)
        #print("setting pi clock to:", end=" ")
        os.system('sudo date -u --set "%s"' % self.date)
        
        
    def get_location(self):
        """Returns the location on earth of the observer

        Returns:
        location: The location
        """
        return self.location

    def get_long(self):
        """Returns the longitude of the observer

        Returns:
        long: The lonogitude
        """
        return self.long

    def get_lat(self):
        """Returns the latitude of the observer

        Returns:
        lat: The latitude
        """
        return self.lat

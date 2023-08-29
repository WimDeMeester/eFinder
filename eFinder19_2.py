#!/usr/bin/python3

# Program to implement an eFinder (electronic finder) on Alt Az telescopes
# Copyright (C) 2023 Keith Venables.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# This variant is customised for ZWO ASI or QHY ccds as camera
# Itrequires a GPS USB dongle, and GPSD & GPS3 installed.
# It requires astrometry.net installed

import subprocess
import time
import os
import math
from PIL import Image
import psutil
import re
from skyfield.api import Star, load
import numpy as np
import threading
import select
from pathlib import Path
import fitsio
import socket
import Coordinates
import Display
import ASICamera
import CameraInterface
import gps_loc
from datetime import datetime

home_path = str(Path.home())
version = "19_2"
os.system('pkill -9 -f eFinder.py') # stops the autostart eFinder program running
x = y = 0  # x, y  define what page the display is showing
deltaAz = deltaAlt = 0
increment = [0, 1, 5, 1, 1]
offset_flag = False
align_count = 0
offset = 640, 480
star_name = "no star"
solve = False
sync_count = 0
pix_scale = 15

raPacket = "03:01:21#"
decPacket = "+89*21:46#"
host = ''
port = 4060
backlog = 5
size = 1024

def lx200Socket():
    global raPacket, decPacket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host,port))
    s.listen(backlog)
    try:
        while True:
            client, address = s.accept()
            data = client.recv(size)
            if data:
                pkt = data.decode("utf-8","ignore")
                #print(pkt,end=": ")
                time.sleep(0.1)
                a = pkt.split('#')
                #print(a)
                for x in a:
                    if x != '':
                        if x == ':GR':
                            #print("sending RA",raPacket)
                            time.sleep(0.1)
                            client.send(bytes(raPacket.encode('ascii')))
                        elif x == ':GD':
                            #print("sending Dec",decPacket)
                            time.sleep(.1)
                            client.send(bytes(decPacket.encode('ascii')))
        
              
    except:
        print('Socket problem')
        client.close()
        exit()

def xy2rd(x, y):  # returns the RA & Dec equivalent to a camera pixel x,y
    result = subprocess.run(
        [
            "wcs-xy2rd",
            "-w",
            home_path + "/Solver/images/capture.wcs",
            "-x",
            str(x),
            "-y",
            str(y),
        ],
        capture_output=True,
        text=True,
    )
    result = str(result.stdout)
    line = result.split("RA,Dec")[1]
    ra, dec = re.findall("[-,+]?\d+\.\d+", line)
    return (float(ra), float(dec))

def pixel2dxdy(pix_x, pix_y):  # converts a pixel position, into a delta angular offset from the image centre
    deg_x = (float(pix_x) - 640) * pix_scale / 3600  # in degrees
    deg_y = (480 - float(pix_y)) * pix_scale / 3600
    dxstr = "{: .1f}".format(float(60 * deg_x))  # +ve if finder is left of Polaris
    dystr = "{: .1f}".format(
        float(60 * deg_y)
    )  # +ve if finder is looking below Polaris
    return (deg_x, deg_y, dxstr, dystr)

def dxdy2pixel(dx, dy):
    pix_x = dx * 3600 / pix_scale + 640
    pix_y = 480 - dy * 3600 / pix_scale
    dxstr = "{: .1f}".format(float(60 * dx))  # +ve if finder is left of Polaris
    dystr = "{: .1f}".format(float(60 * dy))  # +ve if finder is looking below Polaris
    return (pix_x, pix_y, dxstr, dystr)

def imgDisplay():  # displays the captured image on the Pi desktop.
    for proc in psutil.process_iter():
        if proc.name() == "display":
            proc.kill()  # delete any previous image display
    im = Image.open(home_path + "/Solver/images/capture.jpg")
    im.show()

def solveImage():
    global raPacket, decPacket, offset_flag, solve, solvedPos, elapsed_time, star_name, star_name_offset, solved_radec, solved_altaz
    scale_low = str(pix_scale * 0.9)
    scale_high = str(pix_scale * 1.1)
    name_that_star = ([]) if (offset_flag == True) else (["--no-plots"])
    handpad.display("Started solving", "", "")
    limitOptions = [
        "--overwrite",  # overwrite any existing files
        "--skip-solved",  # skip any files we've already solved
        "--cpulimit",
        "10",  # limit to 10 seconds(!). We use a fast timeout here because this code is supposed to be fast
    ]
    optimizedOptions = [
        "--downsample",
        "2",  # downsample 4x. 2 = faster by about 1.0 second; 4 = faster by 1.3 seconds
        "--no-remove-lines",  # Saves ~1.25 sec. Don't bother trying to remove surious lines from the image
        "--uniformize",
        "0",  # Saves ~1.25 sec. Just process the image as-is
    ]
    scaleOptions = [
        "--scale-units",
        "arcsecperpix",  # next two params are in arcsecs. Supplying this saves ~0.5 sec
        "--scale-low",
        scale_low,  # See config above
        "--scale-high",
        scale_high,  # See config above
    ]
    fileOptions = [
        "--new-fits",
        "none",  # Don't create a new fits
        "--solved",
        "none",  # Don't generate the solved output
        "--match",
        "none",  # Don't generate matched output
        "--corr",
        "none",  # Don't generate .corr files
        "--rdls",
        "none",  # Don't generate the point list
    ]    
    #    "--temp-axy",  # We can't specify not to create the axy list, but we can write it to /tmp
    cmd = ["solve-field"]
    captureFile = home_path + "/Solver/images/capture.jpg"
    options = (
        limitOptions + optimizedOptions + scaleOptions + fileOptions + [captureFile]
    )
    start_time = time.time()
    # next line runs the plate-solve on the captured image file
    result = subprocess.run(
        cmd + name_that_star + options, capture_output=True, text=True
    )
    elapsed_time = time.time() - start_time
    print("solve elapsed time " + str(elapsed_time)[0:4] + " sec\n")
    print(result.stdout)  # this line added to help debug.
    result = str(result.stdout)
    if "solved" not in result:
        print("Bad Luck - Solve Failed")
        handpad.display("Not Solved", "", "")
        solve = False
        return
    if (offset_flag == True) and ("The star" in result):
        table, h = fitsio.read(home_path + "/Solver/images/capture.axy", header=True)
        star_name_offset = table[0][0], table[0][1]
        lines = result.split("\n")
        for line in lines:
            if line.startswith("  The star "):
                star_name = line.split(" ")[4]
                print("Solve-field Plot found: ", star_name)
                break
    solvedPos = applyOffset()
    ra, dec, d = solvedPos.apparent().radec(coordinates.get_ts().now())
    solved_radec = ra.hours, dec.degrees
    raPacket = coordinates.hh2dms(solved_radec[0])+'#'
    decPacket = coordinates.dd2aligndms(solved_radec[1])+'#'
    print (raPacket,decPacket)
    solved_altaz = coordinates.conv_altaz(geo, *(solved_radec))
    arr[0, 0][0] = "Sol: RA " + coordinates.hh2dms(solved_radec[0])
    arr[0, 0][1] = "   Dec " + coordinates.dd2dms(solved_radec[1])
    arr[0, 0][2] = "time: " + str(elapsed_time)[0:4] + " s"
    arr[0, 1][0] = "Sol: Az " + coordinates.ddd2dms(solved_altaz[1])
    arr[0, 1][1] = "   Alt " + coordinates.dd2dms(solved_altaz[0])
    arr[0, 1][2] = "time: " + str(elapsed_time)[0:4] + " s"
    solve = True

def applyOffset():
    x_offset, y_offset, dxstr, dystr = dxdy2pixel(
        float(param["d_x"]), float(param["d_y"])
    )
    print('applied_offset_pixels x,y',x_offset,y_offset)
    ra, dec = xy2rd(x_offset, y_offset)
    solved = Star(
        ra_hours=ra / 15, dec_degrees=dec
    )  # will set as J2000 as no epoch input
    solvedPos_scope = (
        geo.get_location().at(coordinates.get_ts().now()).observe(solved)
    )  # now at Jnow and current location
    return solvedPos_scope

def deltaCalc():
    global deltaAz, deltaAlt, elapsed_time
    saved_altaz = coordinates.conv_altaz(geo, *(saved_radec))
    deltaAz = solved_altaz[1] - saved_altaz[1]
    if abs(deltaAz) > 180:
        if deltaAz < 0:
            deltaAz = deltaAz + 360
        else:
            deltaAz = deltaAz - 360
    deltaAz = 60 * (
        deltaAz * math.cos(solved_altaz[0]*math.pi/180)
    )  # actually this is delta'x' in arcminutes
    deltaAlt = solved_altaz[0] - saved_altaz[0]
    deltaAlt = 60 * (deltaAlt)  # in arcminutes
    deltaXstr = "{: .2f}".format(float(deltaAz))
    deltaYstr = "{: .2f}".format(float(deltaAlt))
    arr[0, 2][0] = "Delta: x= " + deltaXstr
    arr[0, 2][1] = "       y= " + deltaYstr
    arr[0, 2][2] = "time: " + str(elapsed_time)[0:4] + " s"

def measure_offset():
    global offset_str, offset_flag, param, scope_x, scope_y, star_name
    offset_flag = True
    handpad.display("started capture", "", "")
    capture()
    imgDisplay()
    solveImage()
    if solve == False:
        handpad.display("solve failed", "", "")
        return
    scope_x = star_name_offset[0]
    scope_y = star_name_offset[1]
    print('pixel_offset x,y',star_name_offset)
    d_x, d_y, dxstr, dystr = pixel2dxdy(scope_x, scope_y)
    param["d_x"] = d_x
    param["d_y"] = d_y
    save_param()
    offset_str = dxstr + "," + dystr
    arr[2, 1][1] = "new " + offset_str
    arr[2, 2][1] = "new " + offset_str
    handpad.display(arr[2, 1][0], arr[2, 1][1], star_name + " found")
    offset_flag = False

def up_down(v):
    global x
    x = x + v
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])

def left_right(v):
    global y
    y = y + v
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])

def up_down_inc(i, sign):
    global increment
    arr[x, y][1] = int(float(arr[x, y][1])) + increment[i] * sign
    param[arr[x, y][0]] = float(arr[x, y][1])
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])
    update_summary()
    time.sleep(0.1)


def flip():
    global param
    arr[x, y][1] = 1 - int(float(arr[x, y][1]))
    param[arr[x, y][0]] = str((arr[x, y][1]))
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])
    update_summary()
    time.sleep(0.1)

def update_summary():
    global param
    arr[1, 0][0] = (
        "Ex:" + str(param["Exposure"]) + "  Gn:" + str(param["Gain"])
    )
    arr[1, 0][1] = "Test mode:" + str(param["Test mode"])
    save_param()

def capture():
    global param
    if param["Test mode"] == "1":
        if offset_flag == False:
            m13 = True
            polaris_cap = False
        else:
            m13 = False
            polaris_cap = True
    else:
        m13 = False
        polaris_cap = False
    radec = "RADec"
    camera.capture(
        int(float(param["Exposure"]) * 1000000),
        int(float(param["Gain"])),
        radec,
        m13,
        polaris_cap,
    )

def go_solve():
    global x, y, solve, arr, saved_radec
    #new_arr = nexus.read_altAz(arr)
    #arr = new_arr
    handpad.display("Image capture", "", "")
    capture()
    imgDisplay()
    handpad.display("Plate solving", "", "")
    solveImage()
    if solve == True:
        handpad.display("Solved", "", "")
    else:
        handpad.display("Not Solved", "", "")
        return
    
    if x == 0 and y == 2:
            try:
                deltaCalc()
            except:
                pass    
            handpad.display(arr[0,2][0], arr[0,2][1], arr[0,2][2])
    else:
        x = 0
        y = 0
        handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])

def save_position():
    global x, y, solve, arr, saved_radec
    #new_arr = nexus.read_altAz(arr)
    #arr = new_arr
    handpad.display("Image capture", "", "")
    capture()
    imgDisplay()
    handpad.display("Plate solving", "", "")
    solveImage()
    if solve == True:
        handpad.display("Solved", "", "")
        saved_radec = solved_radec
    else:
        handpad.display("Not Solved", "", "")
        return
    deltaCalc()
    x = 0
    y = 0
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])


def reset_offset():
    global param, arr
    param["d_x"] = 0
    param["d_y"] = 0
    offset_str = "0,0"
    arr[2,1][1] = "new " + offset_str
    arr[2,2][1] = "new " + offset_str
    handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])
    save_param()

def get_param():
    global param, offset_str
    if os.path.exists(home_path + "/Solver/eFinder.config") == True:
        with open(home_path + "/Solver/eFinder.config") as h:
            for line in h:
                line = line.strip("\n").split(":")
                param[line[0]] = str(line[1])
        pix_x, pix_y, dxstr, dystr = dxdy2pixel(
            float(param["d_x"]), float(param["d_y"])
        )
        offset_str = dxstr + "," + dystr


def save_param():
    global param
    with open(home_path + "/Solver/eFinder.config", "w") as h:
        for key, value in param.items():
            #print("%s:%s\n" % (key, value))
            h.write("%s:%s\n" % (key, value))

def reader():
    global button
    while True:
        if handpad.get_box() in select.select([handpad.get_box()], [], [], 0)[0]:
            button = handpad.get_box().readline().decode("ascii").strip("\r\n")
        time.sleep(0.1)

def home_refresh():
    global x,y
    while True:
        if x == 0 and y == 0:
            time.sleep(1)
        while x ==0 and y==0:
            #nexus.read_altAz(arr)
            #radec = nexus.get_radec()
            #ra = coordinates.hh2dms(radec[0])
            #dec = coordinates.dd2dms(radec[1])
            #handpad.display('Nexus live',' RA:  '+ra, 'Dec: '+dec)
            time.sleep(0.5)
        else:
            handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])
            time.sleep (0.5)
            

# main code starts here

handpad = Display.Handpad(version)
coordinates = Coordinates.Coordinates()
geo = gps_loc.GPSread(handpad, coordinates)
geo.read()

#nexus = Nexus.Nexus(handpad, coordinates)
#nexus.read()
param = dict()
get_param()

# array determines what is displayed, computed and what each button does for each screen.
# [first line,second line,third line, up button action,down...,left...,right...,select button short press action, long press action]
# empty string does nothing.
# example: left_right(-1) allows left button to scroll to the next left screen
# button texts are infact def functions
p = ""
solRaDec = [
    "Sol:RA ",
    "    Dec ",
    "",
    "",
    "up_down(1)",
    "",
    "left_right(1)",
    "go_solve()",
    "save_position()",
]
solAltAz = [
    "Sol: Az ",
    "    Alt ",
    "",
    "",
    "",
    "left_right(-1)",
    "left_right(1)",
    "go_solve()",
    "save_position()",
]
delta = [
    "Delta: Not saved",
    "'OK' solves",
    "'long OK' saves",
    "",
    "",
    "left_right(-1)",
    "",
    "go_solve()",
    "save_position()",
]
polar = [
    "'OK' Bright Star",
    offset_str,
    "",
    "",
    "",
    "left_right(-1)",
    "left_right(1)",
    "measure_offset()",
    "",
]
reset = [
    "'OK' Resets",
    offset_str,
    "",
    "",
    "",
    "left_right(-1)",
    "left_right(1)",
    "reset_offset()",
    "",
]
summary = ["", "", "", "up_down(-1)", "up_down(1)", "", "left_right(1)", "go_solve()", ""]
exp = [
    "Exposure",
    param["Exposure"],
    "",
    "up_down_inc(1,1)",
    "up_down_inc(1,-1)",
    "left_right(-1)",
    "left_right(1)",
    "go_solve()",
    "",
]
gn = [
    "Gain",
    param["Gain"],
    "",
    "up_down_inc(2,1)",
    "up_down_inc(2,-1)",
    "left_right(-1)",
    "left_right(1)",
    "go_solve()",
    "",
]
mode = [
    "Test mode",
    int(param["Test mode"]),
    "",
    "flip()",
    "flip()",
    "left_right(-1)",
    "",
    "go_solve()",
    "",
]
status = [
    "Long: "+"{:7.2f}".format(geo.get_long()),
    "Lat:  "+"{:7.2f}".format(geo.get_lat()),
    "Brightness",
    "up_down(-1)",
    "",
    "",
    "left_right(1)",
    "go_solve()",
    "",
]
bright = [
    "Handpad",
    "Display",
    "Bright Adj",
    "",
    "",
    "left_right(-1)",
    "refresh()",
    "go_solve()",
    "",
]
arr = np.array(
    [
        [solRaDec, solAltAz, delta, solAltAz, solAltAz],
        [summary, exp, gn, mode, mode],
        [status, polar, reset, bright, bright],
    ]
)
update_summary()
deg_x, deg_y, dxstr, dystr = dxdy2pixel(float(param["d_x"]), float(param["d_y"]))
offset_str = dxstr + "," + dystr
#new_arr = nexus.read_altAz(arr)
#arr = new_arr


if param["Camera Type ('QHY' or 'ASI')"]=='ASI':
    import ASICamera
    camera = ASICamera.ASICamera(handpad)
elif param["Camera Type ('QHY' or 'ASI')"]=='QHY':
    import QHYCamera
    camera = QHYCamera.QHYCamera(handpad)

handpad.display("ScopeDog eFinder", "ver " + version, "")
time.sleep(3)
button = ""
handpad.display(arr[x, y][0], arr[x, y][1], arr[x, y][2])

scan = threading.Thread(target=reader)
scan.daemon = True
scan.start()

serve = threading.Thread(target=lx200Socket)
serve.daemon = True
serve.start()

while True:  # next loop looks for button press and sets display option x,y
    if button == "20":
        exec(arr[x, y][7])
    elif button == "21":
        exec(arr[x, y][8])
    elif button == "18":
        exec(arr[x, y][4])
    elif button == "16":
        exec(arr[x, y][3])
    elif button == "19":
        exec(arr[x, y][5])
    elif button == "17":
        exec(arr[x, y][6])
    button = ""
    time.sleep(0.1)

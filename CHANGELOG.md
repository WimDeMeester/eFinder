# Changelog for eFinder software

## Version 22 - “The Minimalist”
[Keith Venables]

This is the the most basic version of my eFinder yet.

No fancy display or controls needed.

Just 1 switch and 3 buttons wired to the GPIO pins.

Either a gps dongle, or a RTC module is required.

The GPS will provide location and set the Pi clock.

Without the GPS, the eFinder will read a default location from efinder.config and use the Pi’s
clock. Hence in this case a RTC module is required to maintain an accurate Pi system clock.

With the switch open circuit, the eFinder runs in a continuous loop, taking images every 10 seconds and passing the solved RA & Dec to a connected SkySafari App.

Button (GPIO16 BCM taken to ground) will cause an immediate image and solve.

Button (GPIO12 BCM taken to ground) will initiate the finder/scope offset measurement routine.

Whereby the brightest star in the eFinder image is assumed to be the star that the main scope is accurately pointing to and the offset of this star position iOS used for all future solves.

A long press on (GPIO20 BCM taken to ground) will safely shut down the Pi.

If the switch is closed, then no looping occurs, but the button operates as above. The switch is wired between BCM pin 21 and ground.

Note all pin numbers are BCM designations and not Board connector pin numbers.

An optional LED and 330ohm series resistor can be wired between BCM pin 26 and ground.

The LED is illuminated while code is running and goes out when the solve is being computed.

SkySafari can connect via ethernet or wifi on port 4060, LX200 classic protocol. Don’t set the SkySafari readout rate to faster than 2 per second, especially if running the Pi as a wifi hotspot.

## Version 21
[Keith Venables]

### VNGUI
- Has layout and font changes to improve legibility.
- Has 3 new buttons
  - Target: Reads current target RA&Dec AltAz held by the Nexus (either its own or one sent by
SkySafari)
  - Set GoTo: Ability to upload a goto target to the Nexus DSC. The fields are filled with
arbitrary values to demonstrate the format required.
  - Save Image: saves last captured image to the folder /Solver/Stills as filename ddmmyy_hhmmss.jpg (datetime is UTC)
- If a Target has been read from the Nexus DSC, then a delta x,y with respect to the target is
calculated and displayed when solving an image.
- Remember delta x,y is not the same as delta Az, Alt. Delta y does equal delta Alt. Delta x
equals delta Az * cos (Alt). Thus dx,dy is what would be seen in the eyepiece.
- Nexus column is now a live display updated every 0.5 seconds
- GoTo++ is now only the “local sync + repeat last goto” version. Experience has shown this
method to be excellent.
- The GoTo++ function waits until the scope has finished moving before continuing, and
displaying ‘goto finished’
- STOP button replaces old ‘Move’ button, which will stop any goto in progress.
- Simplified display autorotate checkbox and entry of manual image rotation.
- Option to display a camera fov box, as well as eyepieces. Box size set in efinder.config. Note
option to display is independent of the eyepiece fields of view ‘FOV indicator’
- On starting the saved offset is now loaded.
- The display of solved time is now in the scrolling report window at bottom right. This window
also now includes more reports.
- While running the GUI, the handpad display shows results, and can be used to trigger
solve/align/goto
- It will run without a handpad connected.
- Tycho2 catalogue option removed from Annotate list. Far too many labels!
- QHY cameras support is included, but not yet tested with an actual camera! Let me know if a problem.

### Handpad version
- efinder ver21 menu.pdf on the google share shows the latest handpad screen menu structure
- Use main_eF1_2.py. Once this is loaded (as main.py) the usual Thonny stop won’t work. To
stop the code (ie for an update) plug in handset with ‘OK’ button pressed.
- display brightness adjusted from handpad.
- Home display, is a live readout of Nexus derived position.
- Home display shows a ’T’ or ’N’ in top right to indicate Nexus align status (Not or Tracking)
- The GoTo++ function waits until the scope has finished moving before continuing, and
displaying ‘goto finished’
- If you use ‘Perspex Ruby’ 3mm thick acrylic for the handset OLED window the display colour
is > 630nm and hence very good for dark adaptation. The contrast is very high and a
brightness level of ‘1’ is probably useable by most.
- The handpad powers up at a bright setting visible in daylight. (Value stored in bright.txt on
Pico). It will stay at this level until the user scrolls down twice (the status display), then it
will adjust to the previously set dim level.

Many thanks to Wim and Mike who have shown the way in restructuring the code into Classes
and other refinements. 

Thanks to others who have given other valuable feedback.

Special thanks to Serge at AstroDevices for strong support and producing Nexus DSC firmware
enhancements as needed. (He is building his own eFinder too)

Thanks to Bentley who has set up a forum for us to discuss and share eFinder experiences and issues. It can be found here https://groups.io/g/eFinder/messages

## Version 20
[Keith Venables]

Version 20 is for use with ServoCat systems only.

### Connection:
Unplug the Nexus to ServoCat USB cable.
Use that cable to connect eFinder to ServoCat.
Connect the eFinder device USB cable to the Nexus USB, change Nexus USB settings to LX200, 9600 baud.
The eFinder connects to the Nexus DSC via USB, and so the Nexus wifi is available for SkySafari etc.

### Use:
Works as previous versions except:
The Nexus to ServoCat USB cable is normally used to command and stop GoTo’s
Now that command comes from the eFinder.
On handpad eFinder, commanding a GoTo causes the eFinder to automatically download the current goto target in the Nexus, and send it to the ServoCat. The Nexus Goto target can be set either from the Nexus keypad, or SkySafari etc.
On GUI eFinder, the same target download from Nexus can be manually requested, but also a new target can be entered directly from the GUI interface.

Ver 20 stores just two index files in ram. (4112 & 4113) if more are needed the increase the ramdisk size accordingly

Creates ramdisk at /var/tmp

```sudo nano /etc/fstab```

	tmpfs /var/tmp tmpfs nodev,nosuid,size=10MB 0 0

In  a terminal: 

```
sudo mount -a

df -h  # to check or reboot
```

## Version 19
[Keith Venables]

This version is the start of a new variant for encoderless, push to scopes.

The eFinder itself uses the same hardware as mainstream eFinder, raspberry pi, camera and hand pad. A different screen menu structure reflects the lack of Nexus DSC.

It does not not connect to a Nexus DSC

It requires a GPS USB dongle.

After it has started it listens on port 4060 for a SkySafari connection over LAN or Wifi. It then provides latest solved RA & Dec to SkySafari up to a rate of about 4 per second.

It has the ability to save a solved position, and then display the delta from that saved position to any future solves.

Its early in development!

In development….

Save all temporary files to ramdisk.
Add a 9 DOF sensor to allow automatic triggering of solve attempts when the scope has a) moved and b)is now stationary.



## Version 18
[Keith Venables]

- Show live Nexus coordinates

## Version 17
[Keith Venables]

## Version 16_3_1
[Keith Venables]

- Bug in check align status: Issue #31
- eFinder does not handle negative declination values #27

## Version 16_3

[Keith Venables]

- Resolved problem with Nexus DSC not returning its own GoTo target coordinates (using LX200 protocol). New Nexus firmware released on 17th Nov 2022
- Cleaned up GUI panel, removing redundant check boxes (finder focallength and goto source). Moved graticule checkbox to same sub-panel other display options.
- Added new test images (test.jpg & polaris.jpg) that match the 50mm default focal length. Removed all code references to choice of 200mm lens.
- Handpad now offers basic functionality even when the GUI is being run. (Solve, Align & Goto++)
- removed bug whereby in test mode the wrong scale was being used to generate offsets.

## Version 16

[Keith Venables]

- Added ability for user to adjust OLED brightness on the handpad. (main.py)
- Fixed a bug where the RA & Dec wasnt being tagged to the saved image file name.
	Nexus.py

## Version 15

[Keith Venables]

- Added support for QHY cameras (only tested so far with a QHY5L-II Mono)
	install the following to ~/Solver
	libqhy.py
	QHYCamera.py
	qhyccd.py
	add extra line to efinder.config.... Camera Type ('QHY' or 'ASI'):ASI
- Added option to choose between Nexus & SkySafari for source of GoTo target.
	add extra line to efinder.config.... SkySafari GoTo++:0
	0 = Nexus, 1 = SkySafari.
- removes option for 200mm focal length finder scope (ie 50mm only)
- removes support for LCD display module (ie OLED only)

## Version 14

[Keith Venables]

- Fixed a bug on the handpad version whereby in the final 'status' screen, use of the up or down buttons crashed the code.

- Fixed a bug that prevents handpad saved exposure & gain preferences from being displayed on the GUI.

- Modified how the handpad display starts when using the GUI version. 

- Fixed a bug on the handpad version whereby a failed solve could result in the previous delta being displayed without a 'failed solve' warning

[Keith Venables]

- Make the handpad work with the VNC GUI version

[Wim De Meester]

- Move the Nexus code to a class outside of the main classes
- Create a Coordinates class to transform RA and dec to AltAz
- Create a handpad class with all code for the display box
- Create CameraInterface and ASICamera class

## Version 13

[Keith Venables, Wim De Meester]

The clock section in the GUI variant is now a thread and runs nice and smooth. (Wim’s code - Thx)

I’ve pulled out all the Nexus communications into a Class method. On boot the code also determines how it can connect to the Nexus, usb or wifi. Thus these variants aren't needed any more. This will make code changes a lot easier.

For instance the Nexus RA can be obtained by single call
ra = Nexus.get(:GR#)

Some Nexus commands don’t produce a reply, so they are

Nexus.write(:P#)

etc

Nexus.read() produces a grab of all the location and time data from the Nexus.

## Version 12

[Keith Venables]

Biggest recent issue has been the realisation that Skyfield wasn't precessing JNow back to J2000, despite it being described and no errors being thrown. This was messing up the align and local sync functions (adding quite a few arc minutes of error). Also could see that various methods of converting from RA & Dec to AltAz were producing different results.

The fix has been a significant change. The eFinder uses JNow exclusively now internally (solver output being precessed immediately) and my own altAz conversion method applied to all cases for consistency.

The rather neat method of finishing a classic goto, by doing a solve and local sync, followed by repeat goto (aka 'goto++'), wasnt consistent. Now realise that the above issues were partly to blame, plus a discovery that the LX200 protocol used to talk to the Nexus has one “target” used for both align and goto. Easily fixed by reading the goto target before the local sync, and then resending it back to the Nexus as part of the goto++.

This goto++ method seems now to be very consistent. The solve & local sync is very accurate (although Serge has a bug in the Nexus DSC for repeated syncs at the same location) and the goto++ results in scope positioning as good as your drive (ServoCat or ScopeDog) can manage. I’m getting about an arc minute.

The Nexus bug affects everybody with a  Nexus DSC - but not many will have noticed! Repeated local syncs result in the Nexus not quite resetting to the required RA & Dec. Can be 1/10 to 1/3 of a degree off. Without the eFinder most users wouldn’t be aware of the error - except the target wouldn’t be centred in the eyepiece. First local sync in any area of the sky is perfect. Serge is on the case.

For a while I have been using the wcs- modules available with the solver to make the offset measurement and application easier. (Eg the solver can return the RA & Dec of any pixel in the image, not just the centre.

I have now modified the initial offset calibration routine. Just align the main scope with any bright, named star, and the eFinder will recognise it and do the calibration. The offset measured can be saved to disk.

The GUI variant can now show the graticule and eyepiece fov centred or offset, rotated to match the view, and overlayed with object annotations (see example below). The GUI got a make over with night vision colours, and a few more buttons and readouts.

An efinder.config file now holds a lot of user specific set up data, mostly used for the GUI variant. The user can list the eyepieces, exposure & gain choices etc.

I’ve now effectively ditched my LCD hand box and changed to a OLED display in a removable hand box. This has 3 lines of very high contrast text. Looks very similar to the Nexus display. The hand box uses a Pi Pico and is connected to the eFinder via standard USB. Photo below.

Also switched to a build using a standard Raspberry Pi 32bit OS (Debian 10). The astroberry based solver didn’t have all the features (licensing) and also the wifi seems much more stable and robust.

Versions 12_3_ are in the share for those with access. The OLED wifi has what looks like redundant code in it, but it is a new interface to ScopeDog. ScopeDog mk2.1 (not yet released) takes over control of the eFinder as part of the standard alignment and goto actions. No user interface needed!

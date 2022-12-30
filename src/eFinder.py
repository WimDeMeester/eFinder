#!/usr/bin/python3

# Program to implement an eFinder (electronic finder) on motorised Alt Az telescopes
# Copyright (C) 2022 Keith Venables.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# This variant is customised for ZWO ASI ccds as camera, Nexus DSC as telescope interface
# It requires astrometry.net installed

import time
from gui import EFinderGUI
from efinder_core import EFinder
import utils
import logging
import argparse
from pathlib import Path
from Nexus import Nexus
from Coordinates import Coordinates
from common import Common
from Display import PrintOutput, SerialOutput
from NexusDebug import NexusDebug
from handpad import HandPad
from common import CameraData, CLIData, AstroData, OffsetData
from datetime import datetime
from NexusInterface import NexusInterface


version_string = "17_0"


# main code starts here
def main(cli_data: CLIData):
    logging.info(f"Options are: {cli_data}")
    cwd_path = Path.cwd()
    pix_scale = 15
    param = EFinder.get_param(cwd_path)
    output = SerialOutput() if cli_data.real_handpad else PrintOutput()
    handpad = HandPad(output, version_string, param)
    coordinates = Coordinates()
    nexus: NexusInterface = Nexus(output, coordinates) if cli_data.real_nexus else NexusDebug(output, coordinates)
    common = Common(cwd_path=cwd_path,
                    images_path=cli_data.images_path,
                    pix_scale=pix_scale,
                    version=version_string, version_suffix="")

    output.display("ScopeDog eFinder", "Ready", "")
    handpad.update_summary()
    _, _, is_aligned, _ = nexus.read_altAz()
    if is_aligned:
        handpad.set_lines(handpad.aligns_pos,
                          "'Select' syncs",
                          "Nexus is aligned",
                          None)

    camera_type = param["Camera Type"] if cli_data.real_camera else 'TEST'
    camera_debug = common.pick_camera('TEST', output, images_path)
    camera = common.pick_camera(camera_type, output, images_path)

    output.display("ScopeDog eFinder", "v" + version_string, "")
    # main program loop, scan buttons and refresh display
    camera_data = CameraData(camera=camera,
                             camera_debug=camera_debug,
                             gain=1,
                             exposure=1,
                             pix_scale=pix_scale,
                             testimage="")
    astro_data = AstroData(nexus=nexus)
    offset_data = OffsetData()

    eFinder = EFinder(handpad, common, coordinates, camera_data, cli_data,
                      astro_data, offset_data, param)
    if cli_data.has_gui:
        gui = EFinderGUI(eFinder)
        gui.start_loop()

    while True:  # next loop looks for button press and sets display option x,y
        time.sleep(0.1)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.basicConfig(
        format="%(asctime)s %(name)s: %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="eFinder")
    parser.add_argument(
        "-fh",
        "--fakehandpad",
        help="Use a fake handpad",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-fn",
        "--fakenexus",
        help="Use a fake nexus",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-fc",
        "--fakecamera",
        help="Use a fake camera",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-g",
        "--hasgui",
        help="Show the GUI",
        default=False,
        action="store_true",
        required=False,
    )

    parser.add_argument(
        "-n",
        "--notmp",
        help="Don't use the /dev/shm temporary directory.\
                (usefull if not on pi)",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-x", "--verbose", help="Set logging to debug mode", action="store_true"
    )
    parser.add_argument(
        "-l", "--log", help="Log to file", action="store_true"
    )
    args = parser.parse_args()
    # add the handlers to the logger
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.log:
        datenow = datetime.now()
        filehandler = f"efinder-{datenow:%Y%m%d-%H_%M_%S}.log"
        fh = logging.FileHandler(filehandler)
        fh.setLevel(logger.level)
        logger.addHandler(fh)

    images_path = Path("/dev/shm")
    if args.notmp:
        images_path = Path('/tmp')

    utils.create_path(images_path)  # create dir if it doesn't yet exist

    cli_data = CLIData(
        not args.fakehandpad, not args.fakecamera, not args.fakenexus,
        images_path, args.hasgui, [], [])
    main(cli_data)

from pathlib import Path
from shutil import copyfile
import time
from CameraInterface import CameraInterface
import zwoasi as asi
from Display import Display
from typing import Dict
import logging


class ASICamera(CameraInterface):
    """The camera class for ASI cameras.  Implements the CameraInterface interface."""

    def __init__(
        self,
        handpad: Display,
        images_path: Path,
        home_path: Path = Path.cwd(),
    ) -> None:
        """Initializes the ASI camera

        Parameters:
        handpad (Display): The link to the handpad
        images_path (Path): The path where captured images will be stored
        home_path (Path): The home path for the camera"""

        self.camType = "ZWO"
        self.handpad = handpad
        self.images_path = images_path
        self.home_path: Path = home_path
        self.stills_path: Path = home_path.joinpath("Stills")
        self.stills_path.mkdir(exist_ok=True)  # create stills dir if not already therew

        # find a camera
        asi.init("/lib/zwoasi/armv7/libASICamera2.so")  # Initialize the ASI library
        num_cameras = asi.get_num_cameras()  # Get the number of connected cameras
        if num_cameras == 0:
            self.handpad.display("Error:", " no camera found", "")
            self.camType = "not found"
            logging.info("camera not found")
            time.sleep(1)
        else:
            asi.list_cameras()
            self.initialize()
            self.handpad.display("ZWO camera found", "", "")
            logging.info("ZWO camera found")
            time.sleep(1)

    def initialize(self) -> None:
        """Initializes the camera and set the needed control parameters"""
        if self.camType == "not found":
            return
        self.camera = asi.Camera(0)  # Initialize the camera
        self.camera.set_control_value(
            asi.ASI_BANDWIDTHOVERLOAD,
            self.camera.get_controls()["BandWidth"]["MinValue"],
        )
        self.camera.disable_dark_subtract()
        self.camera.set_control_value(asi.ASI_WB_B, 99)
        self.camera.set_control_value(asi.ASI_WB_R, 75)
        self.camera.set_control_value(asi.ASI_GAMMA, 50)
        self.camera.set_control_value(asi.ASI_BRIGHTNESS, 50)
        self.camera.set_control_value(asi.ASI_FLIP, 0)
        self.camera.set_image_type(asi.ASI_IMG_RAW8)

    def capture(
        self, exposure_time: float, gain: float, radec: str, extras: Dict
    ) -> None:
        """Capture an image with the camera

        Parameters:
        exposure_time (float): The exposure time in seconds
        gain (float): The gain
        radec (str): The Ra and Dec
        extras (Dict): Additional parameters, this parameter is not used for a real camera"""
        if self.camType == "not found":
            self.handpad.display("camera not found", "", "")
            return

        timestr = time.strftime("%Y%m%d-%H%M%S")
        self.camera.set_control_value(asi.ASI_GAIN, gain)
        self.camera.set_control_value(asi.ASI_EXPOSURE, exposure_time)  # microseconds
        capture_path = self.images_path.joinpath("capture.jpg")
        self.camera.capture(filename=str(capture_path))
        destination_path = self.stills_path.joinpath(f"{timestr}_{radec}.jpg")
        copyfile(str(capture_path), str(destination_path))

    def get_cam_type(self) -> str:
        """Return the type of the camera

        Returns:
        str: The type of the camera"""
        return self.camType

import subprocess
import re
from CameraInterface import CameraInterface
from skyfield.api import load, Star
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple
from NexusInterface import NexusInterface
import logging
import os
import yaml


@dataclass
class CameraData:
    """Class for keeping track of the camera settings"""
    camera: CameraInterface
    camera_debug: CameraInterface
    gain: float
    exposure: float
    pix_scale: float
    testimage: str


@dataclass
class CLIData:
    """Class for keeping track of the command line options"""
    real_handpad: bool
    real_camera: bool
    real_nexus: bool
    images_path: Path
    has_gui: bool


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class ParamData:
    """Class for keeping track of the parameters read from file.
    TODO: could use some 3rd party library to avoid having to enumerate
    all options.
    """
    param = None
    config_path = None

    def __init__(self, param, config_path):
        # check that there are no unknown entries in the param dict
        self.config_path = config_path
        self.param = dotdict(param)

    @classmethod
    def from_param(cls, param):
        """Create a ParamData object from a dict"""
        return cls(**param)


    @staticmethod
    def load_param(cwd_path: Path):
        config_path = Path(cwd_path / "eFinder.config")
        try:
            with open(config_path, "r") as stream:
                param = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
                logging.error(exc)
        return ParamData(param, config_path=config_path)

    def save_param(self, config_path=config_path):
        if config_path is not None:
            with open(self.config_path, 'w') as stream:
                logging.debug("Saving params: {self.param}")
                yaml.dump(self.param, stream)


    def get_dict(self):
         """Return a dict with the parameters if present """
         # import code; code.interact(local=locals())
         return self.param 

    def __str__(self):
        return str(self.param)

    def __getattr__(self, name):
        if name in self.param:
            return self.param[name]
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")



# @define
# class ParamData:
#     """Class for keeping track of the parameters read from file.
#     TODO: could use some 3rd party library to avoid having to enumerate
#     all options.
#     """
#     # not part of the param data
#     _config_path: str
#
#     exposure: float = 1
#     gain: float = 1
#     exp_range: list[str] = Factory(list)
#     gain_range: list[str] = Factory(list) 
#     test_mode: bool = False
#     camera_type: str = ""
#     d_x: float = 0
#     d_y: float = 0
#     altspeed: float = 0
#     azspeed: float = 0
#     default_eyepiece: float = 0
#     default_focal_length: float = 0
#     scope_focal_length: float = 0
#     eyepiece1: str = ""
#     eyepiece2: str = ""
#     eyepiece3: str = ""
#     eyepiece4: str = ""
#
#
#     def __init__(self, param, config_path):
#         # check that there are no unknown entries in the param dict
#         logging.debug(f"all attrs is {dir(self)}")
#         setattr(self, "_config_path", config_path)
#         for key in param:
#             haskey = hasattr(self, key.lower())
#             logging.debug(f"Key = {key}, {key.lower()}")
#             logging.debug(f"{haskey}")
#             logging.debug(f"{key.lower()=}, {param[key]=}")
#             if haskey:
#                 logging.debug(f"The type is {type(getattr(self, key.lower()))}")
#             if key.lower() not in dir(self) and key[0] != "#":
#                 raise ValueError(f"Unknown parameter: {key}")
#             else:
#                 # import code; code.interact(local=locals())
#                 setattr(self, key.lower(), param[key])
#         self.__attrs_init__(config_path)
#
#     @classmethod
#     def from_param(cls, param):
#         """Create a ParamData object from a dict"""
#         return cls(**param)
#
#
#     @staticmethod
#     def load_param(cwd_path: Path):
#         param = dict()
#         config_path = cwd_path / "eFinder.config"
#         if os.path.exists(config_path):
#             with open(config_path) as h:
#                 for line in h:
#                     line = line.strip("\n").split(":")
#                     param[line[0]] = str(line[1])
#         logging.debug(f"Loading params from {config_path}: {param}")
#         return ParamData(param, config_path=config_path)
#
#     def save_param(self):
#         param = self.get_dict()
#         logging.debug(f"Saving params to {self._config_path}: {param}")
#         with open(self._config_path, "w") as h:
#             for key, value in self.get_dict().items():
#                 # logging.info("%s:%s\n" % (key, value))
#                 h.write("%s:%s\n" % (key, value))
#
#     def get_dict(self):
#          """Return a dict with the parameters if present """
#          # import code; code.interact(local=locals())
#          return asdict(self)
#
#     def __str__(self):
#         return str(self.get_dict())
#

@dataclass
class AstroData:
    """Class for keeping track of all astronomically related data"""
    nexus: NexusInterface
    deltaAz: float = 0
    deltaAlt: float = 0
    align_count: int = 0
    sync_count: int = 0
    goto_ra: float = 0
    goto_dec: float = 0
    solved: bool = False
    solved_radec: Tuple[float, float] = 0, 0
    solved_altaz: Tuple[float, float] = 0, 0


@dataclass
class OffsetData:
    """Class for keeping track of offset values"""
    star_name: str = ""
    star_name_offset: Tuple[float, float] = (0.0, 0.0)
    offset: Tuple[float, float] = (0.0, 0.0)
    offset_new: Tuple[float, float] = (0.0, 0.0)
    offset_saved: Tuple[float, float] = (0.0, 0.0)
    offset_reset: Tuple[float, float] = (0.0, 0.0)
    offset_str: str = "0,0"


class Common:
    def __init__(self, cwd_path: Path, images_path: Path, pix_scale,
                 version: str, version_suffix: str):
        self.home_path = cwd_path
        self.images_path = images_path
        self.pix_scale = pix_scale
        self.ts = load.timescale()
        self.version = version + version_suffix

    def get_version(self):
        return self.version

    # returns the RA & Dec (J2000) corresponding to an image x,y pixel
    def xy2rd(self, x, y):
        result = subprocess.run(
            [
                "wcs-xy2rd",
                "-w",
                Path(self.images_path, "capture.wcs"),
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

    # converts an image pixel x,y to a delta x,y in degrees.
    def pixel2dxdy(self, pix_x, pix_y):
        deg_x = (float(pix_x) - 640) * self.pix_scale / 3600  # in degrees
        deg_y = (480 - float(pix_y)) * self.pix_scale / 3600
        # +ve if finder is left of Polaris
        dxstr = "{: .1f}".format(float(60 * deg_x))
        dystr = "{: .1f}".format(
            float(60 * deg_y)
        )  # +ve if finder is looking below Polaris
        return (deg_x, deg_y, dxstr, dystr)

    def dxdy2pixel(self, dx, dy):
        pix_x = dx * 3600 / self.pix_scale + 640
        pix_y = 480 - dy * 3600 / self.pix_scale
        # +ve if finder is left of Polaris
        dxstr = "{: .1f}".format(float(60 * dx))
        # +ve if finder is looking below Polaris
        dystr = "{: .1f}".format(float(60 * dy))
        return (pix_x, pix_y, dxstr, dystr)

    # creates & returns a 'Skyfield star object' at the set offset and adjusted to Jnow
    def applyOffset(self, nexus, offset):
        x_offset, y_offset, dxstr, dystr = self.dxdy2pixel(
            offset[0], offset[1])
        ra, dec = self.xy2rd(x_offset, y_offset)
        solved = Star(
            ra_hours=float(ra) / 15, dec_degrees=float(dec)
        )  # will set as J2000 as no epoch input
        solvedPos_scope = (
            # GUI uses ts.now(), eFinder uses coordinates.get_ts().now()
            nexus.get_location()
            .at(self.ts.now())
            .observe(solved)
        )  # now at Jnow and current location
        return solvedPos_scope

    def deltaCalc(self, nexus_altaz, solved_altaz, scope_alt, delta_az, delta_alt):
        deltaAz = solved_altaz[1] - nexus_altaz[1]
        if abs(delta_az) > 180:
            if delta_az < 0:
                delta_az = delta_az + 360
            else:
                delta_az = delta_az - 360
        # print('cosine scopeAlt',math.cos(scope_alt))
        delta_az = 60 * (
            delta_az * math.cos(scope_alt)
        )  # actually this is delta'x' in arcminutes
        delta_alt = solved_altaz[0] - nexus_altaz[0]
        delta_alt = 60 * (delta_alt)  # in arcminutes
        return delta_az, delta_alt

    def pick_camera(self, camera_type, handpad, images_path) -> CameraInterface:
        camera: CameraInterface = CameraInterface()
        if "ASI" in camera_type:
            import ASICamera
            camera = ASICamera.ASICamera(handpad, images_path)
        elif "QHY" in camera_type:
            import QHYCamera
            camera = QHYCamera.QHYCamera(handpad, images_path)
        elif "TEST" in camera_type:
            import CameraDebug
            camera = CameraDebug.CameraDebug(images_path, images_path)
        return camera

import serial
import sys
import select
from enum import Enum
import logging
from typing import Dict
from curtsies import Input


def determine_serial_port() -> str:
    """ class to determine the serial port """
    import subprocess
    dev_name = "/dev/ttyACM1"
    try:
        result = subprocess.check_output('ls -l /dev/serial/by-id/',shell=True)
        result =(result.decode('ascii')).splitlines()
        for n in range(len(result)):
            if "MicroPython" in result[n]:
                dev_name = "/dev/"+ result[n][-7:]
    except:
        pass
    return dev_name

class DisplayButtons(Enum):
    BTN_SELECT = 21
    DO_SELECT = 7  # does solve mostly
    BTN_LONGSELECT = 20
    DO_LONGSELECT = 8
    BTN_LEFT = 16
    DO_LEFT = 5
    BTN_RIGHT = 18
    DO_RIGHT = 6
    BTN_UP = 17
    DO_UP = 3
    BTN_DOWN = 19
    DO_DOWN = 4


class Output:
    def display(self, line0: str, line1: str, line2: str) -> None:
        """Display the three lines on the display

        Parameters:
        line0 (str): The first line to display
        line1 (str): The second line to display
        line2 (str): The third line to display.  This line is not displayed on the LCD module.
        """
        pass

    def get_button_press(self):
        """Gets the button press from this display

        Returns:
        a numeric value representing the value of the button pressed
        """
        pass


class SerialOutput(Output):
    box: serial.Serial

    def __init__(self, port=determine_serial_port(), baudrate=115200) -> None:
        try:
            logging.debug(f"Connecting serial output, {port=}, {baudrate=}")
            self.box = serial.Serial(
                port,
                baudrate,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                writeTimeout=0,
                timeout=0,
                rtscts=False,
                dsrdtr=False,
            )
        except Exception as ex:
            logging.error("ERROR: no handpad display box found")
            logging.debug(f"{ex=}")
            sys.exit()

    def display(self, line0: str, line1: str, line2: str) -> None:
        if line1 is None:
            line1 = ""
        if type(line1) is int or type(line1) is float: 
            line1 = str(line1)
        self.box.write(bytes(("0:" + line0 + "\n").encode("UTF-8")))
        self.box.write(bytes(("1:" + line1 + "\n").encode("UTF-8")))
        self.box.write(bytes(("2:" + line2 + "\n").encode("UTF-8")))

    def get_button_press(self):
        if self.box in select.select([self.box], [], [], 0)[0]:
            return DisplayButtons(
                int(self.box.readline().decode("ascii").strip("\r\n"))
            )


class PrintOutput(Output):
    nr_chars = 20
    mapping: Dict = dict()

    def __init__(self, mapping_mode="arrows") -> None:
        self.header, header_dashes = self._create_headings(
            self.nr_chars, "Handpad start"
        )
        self.footer, _ = self._create_headings(
            self.nr_chars, "Handpad stop", header_dashes
        )
        self._create_mapping(mapping_mode)

    def _create_headings(self, nr_chars, text, header_dashes=None):
        dashes = (
            int((nr_chars - len(text)) / 2) if header_dashes is None else header_dashes
        )
        return f"{dashes*'-'}{text}{(nr_chars-dashes-len(text))*'-'}\n", dashes

    def display(self, line0: str, line1: str, line2: str) -> None:
        # no logging here because multiline logging is ugly
        print(f"{self.header}{line0}\n{line1}\n{line2}\n{self.footer}")

    def get_button_press(self):
        with Input(keynames="curses") as input_generator:
            res = input_generator.send(None)
        if res in self.mapping:
            return self.mapping[res]
        else:
            logging.debug(f"Unrecognized button pressed: '{res}'")
        return None

    def _create_mapping(self, mapping_mode):
        if mapping_mode == "arrows":
            self.mapping = {
                "KEY_LEFT": DisplayButtons.BTN_LEFT,
                "KEY_RIGHT": DisplayButtons.BTN_RIGHT,
                "KEY_UP": DisplayButtons.BTN_UP,
                "KEY_DOWN": DisplayButtons.BTN_DOWN,
                " ": DisplayButtons.BTN_SELECT,
                "\n": DisplayButtons.BTN_LONGSELECT,
            }
            logging.info(
                "Navigate the handpad using arrow keys, space (select) and enter (long press select)"
            )
        elif mapping_mode == "dvorak":
            self.mapping = {
                "a": DisplayButtons.BTN_LEFT,
                "e": DisplayButtons.BTN_RIGHT,
                ",": DisplayButtons.BTN_UP,
                "o": DisplayButtons.BTN_DOWN,
                "'": DisplayButtons.BTN_SELECT,
                ".": DisplayButtons.BTN_LONGSELECT,
            }
            logging.info(
                "Navigate the handpad using a (left), e (right), ',' (up), o (down), ' (select), . (long press select)"
            )


class Display(Output):
    """All methods to work with the handpad"""

    output: Output

    def __init__(self, output: Output) -> None:
        """Initialize the Handpad class"""
        self.output = output if output is not None else SerialOutput()

    def display(self, line0: str, line1: str, line2: str) -> None:
        self.output.display(line0, line1, line2)

    def get_box(self):
        """Returns the box variable

        Returns:
        serial.Serial: The box variable"""
        return None


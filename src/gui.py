from skyfield.api import load
import tkinter as tk
from tkinter import Label, Radiobutton, StringVar, Checkbutton, Button, Frame
from PIL import Image, ImageTk, ImageDraw, ImageOps
from pathlib import Path
from common import AstroData, CameraData, CLIData, Common, OffsetData
import logging
from Coordinates import Coordinates
import threading
import sys
from efinder_core import EFinder
from NexusInterface import NexusInterface
import re
import time
import math
import os
import glob


class EFinderGUI:
    f_g = "red"
    b_g = "black"
    LST, lbl_LST, lbl_UTC, lbl_date, nexus, sidereal = (
        None,
        None,
        None,
        None,
        None,
        None,
    )
    exposure = 1.0
    # planets and earth not used
    planets = load("de421.bsp")
    earth = planets["earth"]
    ts = load.timescale()
    window = tk.Tk()
    box_list = ["", "", "", "", "", ""]
    eyepieces = None

    def __init__(self, efinder: EFinder):
        self.efinder = efinder
        self.param = efinder.param
        self.camera_data = efinder.camera_data
        self.common = efinder.common
        self.coordinates = efinder.coordinates
        self.cli_data = efinder.cli_data
        self.astro_data: AstroData = efinder.astro_data
        self.nexus: NexusInterface = self.astro_data.nexus
        self.offset_data: OffsetData = efinder.offset_data
        self.cwd_path: Path = Path.cwd()
        self.eyepieces = self.param.eyepieces
        # main program loop, using tkinter GUI
        self.window.title("ScopeDog eFinder v" + self.common.get_version())
        self.window.geometry("1300x1000+100+40")
        self.window.configure(bg="black")
        self.window.bind("<<OLED_Button>>", self.do_button)
        self.setup_sidereal()
        # self.sidereal()

    def start_loop(self):
        self.update_nexus_GUI()
        NexStr = self.nexus.get_nex_str()
        self.draw_screen(NexStr)

    def update_nexus_GUI(self):
        """Put the correct nexus numbers on the GUI."""
        logging.debug("update_nexus_GUI")
        self.nexus.read_altAz()
        nexus_radec = self.nexus.get_radec()
        nexus_altaz = self.nexus.get_altAz()
        tk.Label(
            self.window,
            width=10,
            text=self.coordinates.hh2dms(nexus_radec[0]),
            anchor="e",
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=225, y=804)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.dd2dms(nexus_radec[1]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=225, y=826)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.ddd2dms(nexus_altaz[1]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=225, y=870)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.dd2dms(nexus_altaz[0]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=225, y=892)

    def do_button(self, event):
        # TODO replace the standard handpad operation?
        logging.info(f"do_button with {event=}")

    #     global handpad, coordinates, solved_radec
    #     logging.debug(f"button event: {button}")
    #     if button == "21":
    #         handpad.display("Capturing image", "", "")
    #         read_nexus_and_capture()
    #         handpad.display("Solving image", "", "")
    #         solve()
    #         handpad.display(
    #             "RA:  " + coordinates.hh2dms(solved_radec[0]),
    #             "Dec:" + coordinates.dd2dms(solved_radec[1]),
    #             "d:" + str(deltaAz)[:6] + "," + str(deltaAlt)[:6],
    #         )
    #     elif button == "17":  # up button
    #         handpad.display("Performing", "  align", "")
    #         align()
    #         handpad.display(
    #             "RA:  " + coordinates.hh2dms(solved_radec[0]),
    #             "Dec:" + coordinates.dd2dms(solved_radec[1]),
    #             "Report:" + p,
    #         )
    #     elif button == "19":  # down button
    #         handpad.display("Performing", "   GoTo++", "")
    #         goto()
    #         handpad.display(
    #             "RA:  " + coordinates.hh2dms(solved_radec[0]),
    #             "Dec:" + coordinates.dd2dms(solved_radec[1]),
    #             "d:" + str(deltaAz)[:6] + "," + str(deltaAlt)[:6],
    #         )

    def solve_image_failed(self, b_g=None, f_g=None):
        self.box_write("Solve Failed", True)
        if b_g is None or f_g is None:
            b_g = self.b_g
            f_g = self.f_g
        tk.Label(
            self.window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
        ).place(x=410, y=804)
        tk.Label(
            self.window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
        ).place(x=410, y=826)
        tk.Label(
            self.window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
        ).place(x=410, y=870)
        tk.Label(
            self.window, width=10, anchor="e", text="no solution", bg=b_g, fg=f_g
        ).place(x=410, y=892)

    def solve_image_success(self, solved_radec, solved_altaz):
        tk.Label(
            self.window,
            width=10,
            text=self.coordinates.hh2dms(solved_radec[0]),
            anchor="e",
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=410, y=804)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.dd2dms(solved_radec[1]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=410, y=826)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.ddd2dms(solved_altaz[1]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=410, y=870)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.dd2dms(solved_altaz[0]),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=410, y=892)
        self.deltaCalcGUI()

    def show_elapsed_time(self, elapsed_time):
        """Show the elapsed time in the GUI"""
        tk.Label(
            self.window,
            text=f"{elapsed_time:.2f} s",
            width=20,
            anchor="e",
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=315, y=936)

    def image_show(self):
        img2 = Image.open(self.cli_data.images_path / "capture.jpg")
        width, height = img2.size
        # original is 1280 x 960
        img2 = img2.resize((1014, 760), Image.LANCZOS)
        width, height = img2.size
        # vertical finder field of view in arc min
        h = self.camera_data.pix_scale * 960 / 60
        w = self.camera_data.pix_scale * 1280 / 60
        w_offset = width * self.offset_data.offset[0] * 60 / w
        h_offset = height * self.offset_data.offset[1] * 60 / h
        img2 = img2.convert("RGB")
        if self.grat.get() == "1":
            draw = ImageDraw.Draw(img2)
            draw.line([(width / 2, 0), (width / 2, height)], fill=75, width=2)
            draw.line([(0, height / 2), (width, height / 2)], fill=75, width=2)
            draw.line(
                [(width / 2 + w_offset, 0), (width / 2 + w_offset, height)],
                fill=255,
                width=1,
            )
            draw.line(
                [(0, height / 2 - h_offset), (width, height / 2 - h_offset)],
                fill=255,
                width=1,
            )
        if self.EP.get() == "1":
            draw = ImageDraw.Draw(img2)
            tfov = (
                (
                    float(self.EPlength.get())
                    * height
                    / float(self.param.scope_focal_length)
                )
                * 60
                / h
            ) / 2  # half tfov in pixels
            draw.ellipse(
                [
                    width / 2 + w_offset - tfov,
                    height / 2 - h_offset - tfov,
                    width / 2 + w_offset + tfov,
                    height / 2 - h_offset + tfov,
                ],
                fill=None,
                outline=255,
                width=1,
            )
        if self.lock.get() == "1":
            img2 = self.zoom_at(img2, w_offset, h_offset, 1)
        if self.zoom.get() == "1":
            img2 = self.zoom_at(img2, 0, 0, 2)
        if self.flip.get() == "1":
            img2 = ImageOps.flip(img2)
        if self.mirror.get() == "1":
            img2 = ImageOps.mirror(img2)
        if self.auto_rotate.get() == "1":
            img2 = img2.rotate(self.nexus.get_scope_alt())
        elif self.manual_rotate.get() == "1":
            angle_deg = self.angle.get()
            img2 = img2.rotate(float(angle_deg))
        self.img3 = img2
        self.img2 = ImageTk.PhotoImage(img2)
        self.panel.configure(image=self.img2)
        self.panel.image = self.img2
        self.panel.place(x=200, y=5, width=1014, height=760)

    # GUI specific

    def setup_sidereal(self):
        # global LST, lbl_LST, lbl_UTC, lbl_date, ts, nexus, window
        logging.info("setup_sidereal")
        b_g = self.b_g
        f_g = self.f_g
        t = self.ts.now()
        self.LST = t.gmst + self.nexus.get_long() / 15  # as decimal hours
        LSTstr = (
            str(int(self.LST))
            + "h "
            + str(int((self.LST * 60) % 60))
            + "m "
            + str(int((self.LST * 3600) % 60))
            + "s"
        )
        self.lbl_LST = Label(self.window, bg=b_g, fg=f_g, text=LSTstr)
        self.lbl_LST.place(x=55, y=44)
        self.lbl_UTC = Label(
            self.window, bg=b_g, fg=f_g, text=t.utc_strftime("%H:%M:%S")
        )
        self.lbl_UTC.place(x=55, y=22)
        self.lbl_date = Label(
            self.window, bg=b_g, fg=f_g, text=t.utc_strftime("%d %b %Y")
        )
        self.lbl_date.place(x=55, y=0)

    # GUI specific

    def sidereal(self):
        t = self.ts.now()
        self.LST = t.gmst + self.nexus.get_long() / 15  # as decimal hours
        LSTstr = (
            str(int(self.LST))
            + "h "
            + str(int((self.LST * 60) % 60))
            + "m "
            + str(int((self.LST * 3600) % 60))
            + "s"
        )
        self.lbl_LST.config(text=LSTstr)
        self.lbl_UTC.config(text=t.utc_strftime("%H:%M:%S"))
        self.lbl_date.config(text=t.utc_strftime("%d %b %Y"))
        self.lbl_LST.after(1000, self.sidereal)

    # the offset methods:

    def measure_offset(self):
        """Uses core measure offset but does some GUI stuff + allows measuring
        the offset without immediately setting it.
        """
        # logging.debug(f"Starting measure_offset for star name: {self.offset_data.star_name}")
        (
            success,
            d_x,
            d_y,
            dxstr,
            dystr,
            has_star,
            star_name,
        ) = self.efinder.measure_offset(set_offset=False)

        if not success:
            self.box_write("solve failed", True)
            logging.debug("solve failed")
            return

        if star_name == "":  # display warning in red.
            tk.Label(
                self.window,
                width=8,
                text=star_name,
                anchor="w",
                bg=self.f_g,
                fg=self.b_g,
            ).place(x=115, y=470)
        else:
            tk.Label(
                self.window,
                width=8,
                text=star_name,
                anchor="w",
                bg=self.b_g,
                fg=self.f_g,
            ).place(x=115, y=470)
        self.offset_data.offset_new = d_x, d_y
        logging.debug(f"measure_offset stored: {self.offset_data.offset_new=}")
        self.box_write(star_name)
        self.tk_label(text=f"{dxstr}, {dystr}", width=9, anchor="w", x=110, y=450)

    def save_offset(self):
        self.efinder.save_offset(*self.offset_data.offset)
        self.get_offset()
        self.box_write("offset saved")

    def get_offset(self):
        (
            x_offset_saved,
            y_offset_saved,
            dxstr_saved,
            dystr_saved,
        ) = self.common.dxdy2pixel(float(self.param.d_x), float(self.param.d_y))
        self.tk_label(
            text=dxstr_saved + "," + dystr_saved, width=9, anchor="w", x=110, y=520
        )

    def use_saved_offset(self):
        x_offset_saved, y_offset_saved, dxstr, dystr = self.common.dxdy2pixel(
            float(self.param.d_x), float(self.param.d_y)
        )
        self.offset_data.offset = float(self.param.d_x), float(self.param.d_y)
        self.tk_label(text=dxstr + "," + dystr, width=10, x=70, y=400)

    def tk_label(
        self,
        text,
        width,
        x,
        y,
        b_g=None,
        f_g=None,
        anchor="CENTER",
        clear: bool = False,
    ):
        if b_g is None:
            b_g = self.b_g
        if f_g is None:
            f_g = self.f_g
        if clear:
            tk.Label(
                self.window,
                anchor=anchor,
                text=" " * width,
                bg=b_g,
                fg=f_g,
                width=width,
            ).place(x=x, y=y)

        tk.Label(self.window, text=text, bg=b_g, fg=f_g, width=width).place(x=x, y=y)

    def use_new_offset(self):
        self.offset_data.offset = self.offset_data.offset_new
        x_offset_new, y_offset_new, dxstr, dystr = self.common.dxdy2pixel(
            self.offset_data.offset[0], self.offset_data.offset[1]
        )

        tk.Label(
            self.window, text=dxstr + "," + dystr, bg=self.b_g, fg=self.f_g, width=8
        ).place(x=60, y=400)

    def reset_offset(self):
        self.offset_data.offset = self.offset_data.offset_reset
        self.box_write("offset reset")
        tk.Label(self.window, text="0,0", bg=self.b_g, fg="red", width=8).place(
            x=60, y=400
        )

    def draw_screen(self, NexStr):
        b_g = self.b_g
        f_g = self.f_g
        tk.Label(self.window, text="Date", fg=f_g, bg=b_g).place(x=15, y=0)
        tk.Label(self.window, text="UTC", bg=b_g, fg=f_g).place(x=15, y=22)
        tk.Label(self.window, text="LST", bg=b_g, fg=f_g).place(x=15, y=44)
        tk.Label(self.window, text="Loc:", bg=b_g, fg=f_g).place(x=15, y=66)
        tk.Label(
            self.window,
            width=18,
            anchor="w",
            text=str(self.nexus.get_long())
            + "\u00b0  "
            + str(self.nexus.get_lat())
            + "\u00b0",
            bg=b_g,
            fg=f_g,
        ).place(x=55, y=66)
        img = Image.open(self.cwd_path / "splashscreen.jpeg")
        img = img.resize((1014, 760))
        img = ImageTk.PhotoImage(img)
        self.panel = tk.Label(
            self.window, highlightbackground="red", highlightthickness=2, image=img
        )
        self.panel.place(x=200, y=5, width=1014, height=760)

        exposure_str = StringVar()
        exposure_str.set(str(self.camera_data.exposure))
        exp_frame = Frame(self.window, bg="black")
        exp_frame.place(x=0, y=100)
        tk.Label(exp_frame, text="Exposure", bg=b_g, fg=f_g).pack(padx=1, pady=1)
        expRange = self.param.exp_range
        for i in range(len(expRange)):
            tk.Radiobutton(
                exp_frame,
                text=str(expRange[i]),
                bg=b_g,
                fg=f_g,
                width=7,
                activebackground="red",
                anchor="w",
                highlightbackground="black",
                value=str(expRange[i]),
                variable=exposure_str,
            ).pack(padx=1, pady=1)

        gain = StringVar()
        gain.set(str(self.camera_data.gain))
        gain_frame = Frame(self.window, bg="black")
        gain_frame.place(x=80, y=100)
        tk.Label(gain_frame, text="Gain", bg=b_g, fg=f_g).pack(padx=1, pady=1)
        gainRange = self.param.gain_range
        for i in range(len(gainRange)):
            tk.Radiobutton(
                gain_frame,
                text=str(gainRange[i]),
                bg=b_g,
                fg=f_g,
                width=7,
                activebackground="red",
                anchor="w",
                highlightbackground="black",
                value=float(gainRange[i]),
                variable=gain,
            ).pack(padx=1, pady=1)

        options_frame = Frame(self.window, bg="black")
        options_frame.place(x=20, y=270)
        self.polaris = StringVar()
        self.polaris.set("0")
        tk.Checkbutton(
            options_frame,
            text="Polaris image",
            width=13,
            anchor="w",
            highlightbackground="black",
            activebackground="red",
            bg=b_g,
            fg=f_g,
            variable=self.polaris,
        ).pack(padx=1, pady=1)
        self.m31 = StringVar()
        self.m31.set("0")
        tk.Checkbutton(
            options_frame,
            text="M31 image",
            width=13,
            anchor="w",
            highlightbackground="black",
            activebackground="red",
            bg=b_g,
            fg=f_g,
            variable=self.m31,
        ).pack(padx=1, pady=1)

        self.box_write("ccd is " + self.camera_data.camera.get_cam_type())
        self.box_write("Nexus " + NexStr)

        but_frame = Frame(self.window, bg="black")
        but_frame.place(x=25, y=650)
        tk.Button(
            but_frame,
            text="Align",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            highlightbackground="red",
            bd=0,
            height=2,
            width=10,
            command=self.align,
        ).pack(padx=1, pady=40)
        tk.Button(
            but_frame,
            text="Capture",
            activebackground="red",
            highlightbackground="red",
            bd=0,
            bg=b_g,
            fg=f_g,
            height=2,
            width=10,
            command=self.read_nexus_and_capture,
        ).pack(padx=1, pady=5)
        tk.Button(
            but_frame,
            text="Solve",
            activebackground="red",
            highlightbackground="red",
            bd=0,
            height=2,
            width=10,
            bg=b_g,
            fg=f_g,
            command=self.solve,
        ).pack(padx=1, pady=5)
        tk.Button(
            but_frame,
            text="GoTo: via Align",
            activebackground="red",
            highlightbackground="red",
            bd=0,
            height=2,
            width=10,
            bg=b_g,
            fg=f_g,
            command=self.goto,
        ).pack(padx=1, pady=5)
        tk.Button(
            but_frame,
            text="GoTo: via Move",
            activebackground="red",
            highlightbackground="red",
            bd=0,
            height=2,
            width=10,
            bg=b_g,
            fg=f_g,
            command=self.move,
        ).pack(padx=1, pady=5)

        off_frame = Frame(self.window, bg="black")
        off_frame.place(x=10, y=420)
        tk.Button(
            off_frame,
            text="Measure",
            activebackground="red",
            highlightbackground="red",
            bd=0,
            height=1,
            width=8,
            bg=b_g,
            fg=f_g,
            command=self.measure_offset,
        ).pack(padx=1, pady=1)
        tk.Button(
            off_frame,
            text="Use New",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            highlightbackground="red",
            bd=0,
            height=1,
            width=8,
            command=self.use_new_offset,
        ).pack(padx=1, pady=1)
        tk.Button(
            off_frame,
            text="Save Offset",
            activebackground="red",
            highlightbackground="red",
            bd=0,
            bg=b_g,
            fg=f_g,
            height=1,
            width=8,
            command=self.save_offset,
        ).pack(padx=1, pady=1)
        tk.Button(
            off_frame,
            text="Use Saved",
            activebackground="red",
            highlightbackground="red",
            bd=0,
            bg=b_g,
            fg=f_g,
            height=1,
            width=8,
            command=self.use_saved_offset,
        ).pack(padx=1, pady=1)
        tk.Button(
            off_frame,
            text="Reset Offset",
            activebackground="red",
            highlightbackground="red",
            bd=0,
            bg=b_g,
            fg=f_g,
            height=1,
            width=8,
            command=self.reset_offset,
        ).pack(padx=1, pady=1)
        d_x, d_y, dxstr, dystr = self.common.pixel2dxdy(
            self.offset_data.offset[0], self.offset_data.offset[1]
        )

        tk.Label(self.window, text="Offset:", bg=b_g, fg=f_g).place(x=10, y=400)
        tk.Label(self.window, text="0,0", bg=b_g, fg=f_g, width=6).place(x=60, y=400)

        nex_frame = Frame(self.window, bg="black")
        nex_frame.place(x=250, y=766)
        tk.Button(
            nex_frame,
            text="Nexus",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            highlightbackground="red",
            bd=0,
            command=self.update_nexus_GUI,
        ).pack(padx=1, pady=1)

        tk.Label(self.window, text="delta x,y", bg=b_g, fg=f_g).place(x=345, y=770)
        tk.Label(self.window, text="Solution", bg=b_g, fg=f_g).place(x=435, y=770)
        tk.Label(self.window, text="delta x,y", bg=b_g, fg=f_g).place(x=535, y=770)
        target_frame = Frame(self.window, bg="black")
        target_frame.place(x=620, y=766)
        tk.Button(
            target_frame,
            text="Target",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            highlightbackground="red",
            bd=0,
            command=self.readTarget,
        ).pack(padx=1, pady=1)

        dis_frame = Frame(self.window, bg="black")
        dis_frame.place(x=800, y=765)
        tk.Button(
            dis_frame,
            text="Display",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="red",
            bd=0,
            width=8,
            command=self.image_show,
        ).pack(padx=1, pady=1)
        self.grat = StringVar()
        self.grat.set("0")
        tk.Checkbutton(
            dis_frame,
            text="graticule",
            width=10,
            anchor="w",
            highlightbackground="black",
            activebackground="red",
            bg=b_g,
            fg=f_g,
            variable=self.grat,
        ).pack(padx=1, pady=1)
        self.lock = StringVar()
        self.lock.set("0")
        tk.Checkbutton(
            dis_frame,
            text="Scope centre",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=10,
            variable=self.lock,
        ).pack(padx=1, pady=1)
        self.zoom = StringVar()
        self.zoom.set("0")
        tk.Checkbutton(
            dis_frame,
            text="zoom x2",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=10,
            variable=self.zoom,
        ).pack(padx=1, pady=1)
        self.flip = StringVar()
        self.flip.set("0")
        tk.Checkbutton(
            dis_frame,
            text="flip",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=10,
            variable=self.flip,
        ).pack(padx=1, pady=1)
        self.mirror = StringVar()
        self.mirror.set("0")
        tk.Checkbutton(
            dis_frame,
            text="mirror",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=10,
            variable=self.mirror,
        ).pack(padx=1, pady=1)
        self.auto_rotate = StringVar()
        self.auto_rotate.set("0")
        tk.Checkbutton(
            dis_frame,
            text="auto-rotate",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=10,
            variable=self.auto_rotate,
        ).pack(padx=1, pady=1)
        self.manual_rotate = StringVar()
        self.manual_rotate.set("1")
        tk.Checkbutton(
            dis_frame,
            text="rotate angle",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=10,
            variable=self.manual_rotate,
        ).pack(padx=1, pady=1)
        self.angle = StringVar()
        self.angle.set("0")
        tk.Entry(
            dis_frame,
            textvariable=self.angle,
            bg="red",
            fg=b_g,
            highlightbackground="red",
            bd=0,
            width=5,
        ).pack(padx=10, pady=1)

        self.ann_frame = Frame(self.window, bg="black")
        self.ann_frame.place(x=950, y=765)
        tk.Button(
            self.ann_frame,
            text="Annotate",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="red",
            bd=0,
            width=6,
            command=self.annotate_image,
        ).pack(padx=1, pady=1)
        self.bright = StringVar()
        self.bright.set("0")
        tk.Checkbutton(
            self.ann_frame,
            text="Bright",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=8,
            variable=self.bright,
        ).pack(padx=1, pady=1)
        self.hip = StringVar()
        self.hip.set("0")
        tk.Checkbutton(
            self.ann_frame,
            text="Hip",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=8,
            variable=self.hip,
        ).pack(padx=1, pady=1)
        self.hd = StringVar()
        self.hd.set("0")
        tk.Checkbutton(
            self.ann_frame,
            text="H-D",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=8,
            variable=self.hd,
        ).pack(padx=1, pady=1)
        self.ngc = StringVar()
        self.ngc.set("0")
        tk.Checkbutton(
            self.ann_frame,
            text="ngc/ic",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=8,
            variable=self.ngc,
        ).pack(padx=1, pady=1)
        self.abell = StringVar()
        self.abell.set("0")
        tk.Checkbutton(
            self.ann_frame,
            text="Abell",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=8,
            variable=self.abell,
        ).pack(padx=1, pady=1)
        self.tycho2 = StringVar()
        self.tycho2.set("0")
        tk.Checkbutton(
            self.ann_frame,
            text="Tycho2",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=8,
            variable=self.tycho2,
        ).pack(padx=1, pady=1)

        tk.Label(self.window, text="RA", bg=b_g, fg=f_g).place(x=200, y=804)
        tk.Label(self.window, text="Dec", bg=b_g, fg=f_g).place(x=200, y=826)
        tk.Label(self.window, text="Az", bg=b_g, fg=f_g).place(x=200, y=870)
        tk.Label(self.window, text="Alt", bg=b_g, fg=f_g).place(x=200, y=892)

        self.EP = StringVar()
        self.EP.set("0")
        EP_frame = Frame(self.window, bg="black")
        EP_frame.place(x=1060, y=770)
        rad13 = Checkbutton(
            EP_frame,
            text="FOV indicator",
            bg=b_g,
            fg=f_g,
            activebackground="red",
            anchor="w",
            highlightbackground="black",
            bd=0,
            width=20,
            variable=self.EP,
        ).pack(padx=1, pady=2)
        self.EPlength = StringVar()
        self.EPlength.set(float(self.param.default_eyepiece))
        for i in range(len(self.eyepieces)):
            tk.Radiobutton(
                EP_frame,
                text=self.eyepieces[i]["name"],
                bg=b_g,
                fg=f_g,
                activebackground="red",
                anchor="w",
                highlightbackground="black",
                bd=0,
                width=20,
                value=self.eyepieces[i]["mm"] * self.eyepieces[i]["fov"],
                variable=self.EPlength,
            ).pack(padx=1, pady=0)
        self.get_offset()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def on_closing(self):
        self.param.save_param()
        self.efinder.handpad.display.display("Program closed", "via VNCGUI", "")
        sys.exit()

    def zoom_at(self, img, x, y, zoom):
        w, h = img.size
        dh = (h - (h / zoom)) / 2
        dw = (w - (w / zoom)) / 2
        img = img.crop((dw + x, dh - y, w - dw + x, h - dh - y))
        return img.resize((w, h), Image.LANCZOS)

    def align(self):
        msg, p = self.efinder.align()
        for message in msg:
            # show messages
            self.box_write(message)
            tk.Label(self.window, text=message).place(x=20, y=680)
        # status updates
        tk.Label(
            self.window,
            text="align count: " + str(self.astro_data.align_count),
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=20, y=600)
        tk.Label(
            self.window, text="Nexus report: " + p[0:3], bg=self.b_g, fg=self.f_g
        ).place(x=20, y=620)
        self.update_nexus_GUI()
        self.deltaCalcGUI()

    def read_nexus_and_capture(self):
        self.update_nexus_GUI()
        extras = {}
        if self.polaris.get() == "1":
            extras["testimage"] = "polaris"
        elif self.m31.get() == "1":
            extras["testimage"] = "m31"
        logging.debug(f"Calling capture with {extras=}")

        self.efinder.capture(extras=extras)
        self.image_show()

    def solve(self):
        (
            solved,
            has_star,
            star_name,
            elapsed_time,
            solved_radec,
        ) = self.efinder.solveImage()
        self.show_elapsed_time(elapsed_time)
        self.show_solved_coordinates(solved_radec)

        if not solved:
            solve_image_failed(b_g, f_g)
            return
        logging.debug(f"Found star is {star_name}")
        if star_name == "":
            self.box_write(" no named star")
        else:
            self.box_write(f"{star_name} found")
        self.box_write("solved")
        self.deltaCalcGUI()
        self.readTarget()
        logging.debug("Solve done")

    # TODO
    def goto(self):
        self.readTarget()  # reads goto_ra and goto_dec
        self.efinder.align()  # local sync scope to true RA & Dec
        if solved == False:
            eFinderGUI.box_write("solve failed", True)
            return
        self.astro_data.nexus.write(":Sr" + goto_ra + "#")
        self.astro_data.nexus.write(":Sd" + goto_dec + "#")
        reply = self.astro_data.nexus.get(":MS#")
        time.sleep(0.1)
        self.box_write("moving scope", True)

    # UI only method
    def move(self):
        self.efinder.solveImage()
        self.image_show()
        if self.astro_data.solved:
            self.box_write("no solution yet")
            return
        goto_ra = self.nexus.get(":Gr#").split(":")
        goto_dec = re.split(r"[:*]", self.nexus.get(":Gd#"))
        # not a valid goto target set yet.
        if goto_ra[0] == "00" and goto_ra[1] == "00":
            self.box_write("no GoTo target")
            return
        logging.info("%s %s %s" % ("goto RA & Dec", goto_ra, goto_dec))
        ra = float(goto_ra[0]) + float(goto_ra[1]) / 60 + float(goto_ra[2]) / 3600
        dec = float(goto_dec[0]) + float(goto_dec[1]) / 60 + float(goto_dec[2]) / 3600
        logging.info("%s %s %s" % ("lgoto radec", ra, dec))
        alt_g, az_g = self.coordinates.conv_altaz(
            self.nexus.get_long(), self.nexus.get_lat(), ra, dec
        )
        logging.info("%s %s %s" % ("target Az Alt", az_g, alt_g))
        delta_Az = (az_g - self.astro_data.solved_altaz[1]) * 60  # +ve move scope right
        delta_Alt = (alt_g - self.astro_data.solved_altaz[0]) * 60  # +ve move scope up
        delta_Az_str = "{: .2f}".format(delta_Az)
        delta_Alt_str = "{: .2f}".format(delta_Alt)
        logging.info(f"deltaAz: {delta_Az_str}, deltaAlt: {delta_Alt_str}")
        self.box_write(f"deltaAz : {delta_Az_str}")
        self.box_write(f"deltaAlt: {delta_Alt_str}")
        self.moveScope(delta_Az, delta_Alt)
        # could insert a new capture and solve?

    # UI only method
    def moveScope(self, dAz, dAlt):
        azPulse = abs(dAz / float(self.param.az_speed))  # seconds
        altPulse = abs(dAlt / float(self.param.alt_speed))
        logging.debug(
            "%s %.2f  %s  %.2f %s"
            % ("azPulse:", azPulse, "altPulse:", altPulse, "seconds")
        )
        self.nexus.write("#:RG#")  # set move speed to guide
        self.box_write("moving scope in Az")
        logging.info("moving scope in Az")
        if dAz > 0:  # if +ve move scope left
            self.nexus.write("#:Me#")
            time.sleep(azPulse)
            self.nexus.write("#:Q#")
        else:
            self.nexus.write("#:Mw#")
            time.sleep(azPulse)
            self.nexus.write("#:Q#")
        time.sleep(0.2)
        self.box_write("moving scope in Alt")
        logging.info("moving scope in Alt")
        self.nexus.write("#:RG#")
        if dAlt > 0:  # if +ve move scope down
            self.nexus.write("#:Ms#")
            time.sleep(altPulse)
            self.nexus.write("#:Q#")
        else:
            self.nexus.write("#:Mn#")
            time.sleep(altPulse)
            self.nexus.write("#:Q#")
        self.box_write("move finished")
        logging.info("move finished")
        time.sleep(1)

    def annotate_image(self):
        # global img3, bright, hip, hd, abell, ngc, tycho2
        scale_low = str(
            self.camera_data.pix_scale * 0.9 * 1.2
        )  # * 1.2 is because image has been resized for the display panel
        scale_high = str(self.camera_data.pix_scale * 1.1 * 1.2)
        self.image_show()
        self.img3 = self.img3.save(self.cli_data.images_path / "adjusted.jpg")
        # first need to re-solve the image as it is presented in the GUI, saved as 'adjusted.jpg'
        annotate_cmd = (
            "solve-field --no-plots --new-fits none --solved none --match none --corr none \
                --rdls none --cpulimit 10 --temp-axy --overwrite --downsample 2 --no-remove-lines --uniformize 0 \
                --scale-units arcsecperpix --scale-low "
            + scale_low
            + " \
                --scale-high "
            + scale_high
            + " "
            + str(self.cli_data.images_path / "adjusted.jpg")
        )
        logging.debug(f"Annotating image with cmd: {annotate_cmd}")
        os.system(annotate_cmd)
        # now we can annotate the image adjusted.jpg
        opt1 = " " if self.bright.get() == "1" else " --no-bright"
        opt2 = (
            " --hipcat=/usr/local/astrometry/annotate_data/hip.fits --hiplabel"
            if self.hip.get() == "1"
            else " "
        )
        opt3 = (
            " --hdcat=/usr/local/astrometry/annotate_data/hd.fits"
            if self.hd.get() == "1"
            else " "
        )
        opt4 = (
            " --abellcat=/usr/local/astrometry/annotate_data/abell-all.fits"
            if self.abell.get() == "1"
            else " "
        )
        opt5 = (
            " --tycho2cat=/usr/local/astrometry/annotate_data/tycho2.kd"
            if self.tycho2.get() == "1"
            else " "
        )
        opt6 = " " if self.ngc.get() == "1" else " --no-ngc"
        try:  # try because the solve may have failed to produce adjusted.jpg
            cmd = (
                'python3 /usr/local/astrometry/lib/python/astrometry/plot/plotann.py \
                    --no-grid --tcolor="orange" --tsize="14" --no-const'
                + opt1
                + opt2
                + opt3
                + opt4
                + opt5
                + opt6
                + " "
                + " ".join(
                    [
                        str(self.cli_data.images_path / "adjusted.wcs"),
                        str(self.cli_data.images_path / "adjusted.jpg"),
                        str(self.cli_data.images_path / "adjusted_out.jpg"),
                    ]
                )
            )
            logging.debug(f"plotann cmd: {cmd}")
            os.system(cmd)
        except:
            logging.debug("Exception during plotann")
            pass
        if os.path.exists(self.cli_data.images_path / "adjusted_out.jpg") == True:
            img3 = Image.open(self.cli_data.images_path / "adjusted_out.jpg")
            filelist = glob.glob(str(self.cli_data.images_path / "adjusted*.*"))
            for filePath in filelist:
                try:
                    os.remove(filePath)
                except:
                    logging.error("problem while deleting file :", filePath)
            self.box_write("annotation successful")
            img4 = ImageTk.PhotoImage(img3)
            self.panel.configure(image=img4)
            self.panel.image = img4
            self.panel.place(x=200, y=5, width=1014, height=760)
        else:
            self.box_write("solve failure")
            return

    def readTarget(self):
        """read from nexus if there's a target set"""
        goto_ra = self.nexus.get(":Gr#")
        goto_dec = self.nexus.get(":Gd#")
        if (
            goto_ra[0:2] == "00" and goto_ra[3:5] == "00"
        ):  # not a valid goto target set yet.
            self.box_write("no GoTo target")
            return
        ra = goto_ra.split(":")
        dec = re.split(r"[:*]", goto_dec)
        logging.info(f"GoTo target: {goto_ra=} {goto_dec=}")
        goto_radec = (
            float(ra[0]) + float(ra[1]) / 60 + float(ra[2]) / 3600
        ), math.copysign(
            abs(abs(float(dec[0])) + float(dec[1]) / 60 + float(dec[2]) / 3600),
            float(dec[0]),
        )
        solved_altaz = self.astro_data.solved_altaz
        scope_alt_rad = solved_altaz[0] * math.pi / 180
        goto_altaz = self.coordinates.conv_altaz(
            self.astro_data.nexus.get_long(),
            self.astro_data.nexus.get_lat(),
            *(goto_radec),
        )
        self.show_goto_target_and_diff(
            goto_radec, goto_altaz, self.efinder.astro_data.solved_altaz, scope_alt_rad
        )

    def show_solved_coordinates(self, solved_radec):
        solved_altaz = self.coordinates.conv_altaz(
            self.astro_data.nexus.get_long(),
            self.astro_data.nexus.get_lat(),
            *(solved_radec),
        )

        b_g = self.b_g
        f_g = self.f_g
        tk.Label(
            self.window,
            width=10,
            text=self.coordinates.hh2dms(solved_radec[0]),
            anchor="e",
            bg=b_g,
            fg=f_g,
        ).place(x=410, y=804)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.dd2dms(solved_radec[1]),
            bg=b_g,
            fg=f_g,
        ).place(x=410, y=826)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.ddd2dms(solved_altaz[1]),
            bg=b_g,
            fg=f_g,
        ).place(x=410, y=870)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.dd2dms(solved_altaz[0]),
            bg=b_g,
            fg=f_g,
        ).place(x=410, y=892)

    def show_goto_target_and_diff(
        self, goto_radec, goto_altaz, solved_altaz, scope_alt_rad
    ):
        b_g = self.b_g
        f_g = self.f_g
        tk.Label(
            self.window,
            width=10,
            text=self.coordinates.hh2dms(goto_radec[0]),
            anchor="e",
            bg=b_g,
            fg=f_g,
        ).place(x=605, y=804)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.dd2dms(goto_radec[1]),
            bg=b_g,
            fg=f_g,
        ).place(x=605, y=826)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.ddd2dms(goto_altaz[1]),
            bg=b_g,
            fg=f_g,
        ).place(x=605, y=870)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=self.coordinates.dd2dms(goto_altaz[0]),
            bg=b_g,
            fg=f_g,
        ).place(x=605, y=892)
        dt_Az = solved_altaz[1] - goto_altaz[1]
        if abs(dt_Az) > 180:
            if dt_Az < 0:
                dt_Az = dt_Az + 360
            else:
                dt_Az = dt_Az - 360
        # actually this is delta'x' in arcminutes
        dt_Az = 60 * (dt_Az * math.cos(scope_alt_rad))
        dt_Alt = solved_altaz[0] - goto_altaz[0]
        dt_Alt = 60 * (dt_Alt)  # in arcminutes
        dt_Azstr = "{: .1f}".format(float(dt_Az)).ljust(8)[:8]
        dt_Altstr = "{: .1f}".format(float(dt_Alt)).ljust(8)[:8]
        tk.Label(
            self.window, width=10, anchor="e", text=dt_Azstr, bg=b_g, fg=f_g
        ).place(x=500, y=870)
        tk.Label(
            self.window, width=10, anchor="e", text=dt_Altstr, bg=b_g, fg=f_g
        ).place(x=500, y=892)

    def box_write(self, new_line):
        t = self.ts.now()
        for i in range(5, 0, -1):
            self.box_list[i] = self.box_list[i - 1]
        self.box_list[0] = (t.utc_strftime("%H:%M:%S ") + new_line).ljust(36)[:35]
        for i in range(0, 5, 1):
            tk.Label(
                self.window, text=self.box_list[i], bg=self.b_g, fg=self.f_g
            ).place(x=1050, y=980 - i * 16)

    def deltaCalcGUI(self):
        """do the core delta calc, then update GUI"""
        self.efinder.deltaCalc()
        deltaAzstr = "{: .1f}".format(float(self.astro_data.deltaAz)).ljust(8)[:8]
        deltaAltstr = "{: .1f}".format(float(self.astro_data.deltaAlt)).ljust(8)[:8]
        tk.Label(
            self.window, width=10, anchor="e", text=deltaAzstr, bg=self.b_g, fg=self.f_g
        ).place(x=315, y=870)
        tk.Label(
            self.window,
            width=10,
            anchor="e",
            text=deltaAltstr,
            bg=self.b_g,
            fg=self.f_g,
        ).place(x=315, y=892)

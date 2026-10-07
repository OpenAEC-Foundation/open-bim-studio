#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Drive the interactive BIM slice through real X11 input and capture it.

Starts a built `main.dl` binary, finds its window, and sends pointer and key
events through the XTEST extension, the way a person would: draw four walls
with the wall tool (one by a typed length), place two windows, drag a corner
with the select tool, undo and redo, hover a wall, orbit the 3D view and
export IFC. A screenshot is saved after every stage; the screenshots and the
status bar they show are the evidence for the interaction. The exported file
is checked with IfcOpenShell and then removed.

The editor writes `bim-slice.ifc` into the repository root, so the driver
refuses to start when that file already exists. Run it against a nested X
server such as `Xephyr :97`, not the desktop session: XTEST moves the real
pointer of the display it is sent to. Requires python-xlib and Pillow.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import time

import ifcopenshell
from Xlib import X, XK, display
from Xlib.ext import xtest
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
TITLE = "BIM slice"

# The plan's initial view, as set up in main.dl for a 1280 x 820 window:
# the plan panel spans 58% of the width between the 44 px status bar and the
# 30 px help line, centred on model point (3, 2) at 60 px per metre.
WIDTH, HEIGHT = 1280, 820
PLAN_RIGHT = WIDTH * 0.58
TOP, BOTTOM = 44.0, HEIGHT - 30.0
CENTRE = (3.0, 2.0)
SCALE = 60.0


def plan_pixel(x: float, y: float) -> tuple[int, int]:
    middle_x = PLAN_RIGHT * 0.5
    middle_y = (TOP + BOTTOM) * 0.5
    return round(middle_x + (x - CENTRE[0]) * SCALE), round(middle_y - (y - CENTRE[1]) * SCALE)


class Driver:
    def __init__(self, window_id: int):
        self.display = display.Display()
        self.window = self.display.create_resource_object("window", window_id)
        self.window.set_input_focus(X.RevertToParent, X.CurrentTime)
        self.window.configure(stack_mode=X.Above)
        self.display.sync()
        time.sleep(0.3)

    def origin(self) -> tuple[int, int]:
        place = self.window.translate_coords(self.display.screen().root, 0, 0)
        return -place.x, -place.y

    def move(self, x: float, y: float) -> None:
        self.move_pixel(*plan_pixel(x, y))

    def move_pixel(self, x: int, y: int) -> None:
        left, top = self.origin()
        xtest.fake_input(self.display, X.MotionNotify, x=left + x, y=top + y)
        self.display.sync()
        time.sleep(0.08)

    def click(self, x: float, y: float) -> None:
        self.move(x, y)
        self.button_down()
        self.button_up()

    def button_down(self, button: int = 1) -> None:
        xtest.fake_input(self.display, X.ButtonPress, button)
        self.display.sync()
        time.sleep(0.08)

    def button_up(self, button: int = 1) -> None:
        xtest.fake_input(self.display, X.ButtonRelease, button)
        self.display.sync()
        time.sleep(0.08)

    def key(self, name: str) -> None:
        code = self.display.keysym_to_keycode(XK.string_to_keysym(name))
        xtest.fake_input(self.display, X.KeyPress, code)
        self.display.sync()
        time.sleep(0.06)
        xtest.fake_input(self.display, X.KeyRelease, code)
        self.display.sync()
        time.sleep(0.06)

    def capture(self, path: Path) -> None:
        geometry = self.window.get_geometry()
        image = self.window.get_image(0, 0, geometry.width, geometry.height, X.ZPixmap, 0xFFFFFFFF)
        Image.frombytes("RGB", (geometry.width, geometry.height), image.data, "raw", "BGRX").save(path)
        print(f"captured {path}")


def find_window(name: str, timeout: float = 20.0) -> int:
    connection = display.Display()
    deadline = time.time() + timeout
    while time.time() < deadline:
        pending = [connection.screen().root]
        while pending:
            window = pending.pop()
            if window.get_wm_name() == name:
                return window.id
            pending.extend(window.query_tree().children)
        time.sleep(0.25)
    raise SystemExit(f"no window named {name!r} appeared")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path, help="directory for the screenshots")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    exported = ROOT / "bim-slice.ifc"
    if exported.exists():
        raise SystemExit(f"{exported} exists; move it away before driving the editor")
    process = subprocess.Popen([str(args.binary.resolve())], cwd=ROOT)
    try:
        driver = Driver(find_window(TITLE))
        time.sleep(0.5)
        driver.key("w")
        for x, y in ((0.0, 0.0), (6.0, 0.0), (6.0, 4.0)):
            driver.click(x, y)
        # The last wall of the outline before closing is typed: pointing west
        # from (6, 4) and typing 6 places the corner at (0, 4).
        driver.move(2.0, 4.0)
        driver.key("6")
        driver.key("Return")
        driver.click(0.0, 0.0)
        driver.key("Escape")
        driver.move(3.0, 1.0)
        driver.capture(args.output / "1-walls.png")
        driver.key("o")
        driver.click(1.5, 0.0)
        driver.click(4.0, 4.0)
        driver.move(3.0, 2.0)
        driver.capture(args.output / "2-windows.png")
        driver.key("s")
        driver.move(6.0, 0.0)
        driver.button_down()
        for step in range(1, 11):
            driver.move(6.0 + 0.1 * step, -0.05 * step)
        driver.capture(args.output / "3-dragging.png")
        driver.button_up()
        driver.key("z")
        driver.move(3.0, 2.0)
        driver.capture(args.output / "4-undone.png")
        driver.key("y")
        driver.move(3.0, 2.1)
        driver.capture(args.output / "5-redone.png")
        # Hovering a wall shows its associative length, measured between its
        # start and finish features.
        driver.move(5.0, 4.0)
        driver.capture(args.output / "6-hover.png")
        # Right-dragging over the 3D panel orbits the view.
        driver.move_pixel(1000, 600)
        driver.button_down(3)
        for step in range(1, 9):
            driver.move_pixel(1000 + 15 * step, 600 - 5 * step)
        driver.button_up(3)
        driver.capture(args.output / "7-orbit.png")
        driver.key("x")
        time.sleep(0.5)
        driver.capture(args.output / "8-exported.png")
        if process.poll() is not None:
            raise SystemExit(f"the editor exited with {process.returncode}")
        if not exported.exists():
            raise SystemExit("pressing X wrote no IFC file")
        model = ifcopenshell.open(str(exported))
        counts = {kind: len(model.by_type(kind)) for kind in ("IfcWall", "IfcOpeningElement", "IfcWindow")}
        print("exported " + " ".join(f"{kind}={count}" for kind, count in counts.items()))
        if counts != {"IfcWall": 4, "IfcOpeningElement": 2, "IfcWindow": 2}:
            raise SystemExit("the exported model does not hold the drawn walls and windows")
    finally:
        process.terminate()
        process.wait(timeout=10)
        exported.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

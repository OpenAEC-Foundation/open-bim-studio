#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Opens the built editor with the connection showcase under a nested X server
and saves screenshots of the 3D view: the whole structure, then the view
orbited and zoomed toward chosen connections. Run against Xephyr, never the
desktop session, because XTEST moves the pointer of the display it is sent
to:

    Xephyr :97 -screen 1400x900 &
    DISPLAY=:97 python3 look_connections.py BINARY OUTPUT_DIR [--example ARG]
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time

from Xlib import X
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drive_gui import Driver, find_window, ROOT, TITLE, WIDTH, HEIGHT, PLAN_RIGHT, TOP, BOTTOM  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--example", default="--connections-example")
    parser.add_argument("--settle", type=float, default=90.0, help="seconds to wait for the first evaluation")
    parser.add_argument("--camera", action="append", default=[], metavar="YAW PITCH X Y Z SCALE",
                        help="a 3D view to capture, passed on to the editor; repeatable")
    parser.add_argument("--label", action="append", default=[], dest="labels", help="a name per --camera, in order")
    parser.add_argument("--edges", action="store_true", help="show the 3D view with edges (Ctrl+2)")
    parser.add_argument("--extra", action="append", default=[], metavar="ARG",
                        help="a further argument for the editor, such as --hide Columns; repeatable")
    args = parser.parse_args()
    if len(args.labels) < len(args.camera):
        args.labels += [f"camera{index}" for index in range(len(args.labels), len(args.camera))]
    args.output.mkdir(parents=True, exist_ok=True)

    def capture(driver: Driver, path: Path) -> None:
        # The root window: a window the server cannot read gives BadMatch.
        root = driver.display.screen().root
        geometry = root.get_geometry()
        image = root.get_image(0, 0, geometry.width, geometry.height, X.ZPixmap, 0xFFFFFFFF)
        Image.frombytes("RGB", (geometry.width, geometry.height), image.data, "raw", "BGRX").save(path)
        print(f"captured {path}", flush=True)

    command = [str(args.binary.resolve()), args.example]
    for extra in args.extra:
        command += extra.split()
    for preset in args.camera:
        command += ["--camera", *preset.split()]
    process = subprocess.Popen(command, cwd=ROOT)
    try:
        driver = Driver(find_window(TITLE, timeout=60.0))
        time.sleep(args.settle)
        view_x = (PLAN_RIGHT + WIDTH) * 0.5
        view_y = (TOP + BOTTOM) * 0.5
        driver.key("f")
        time.sleep(1.0)
        capture(driver, args.output / "1-overview.png")
        # Orbit: right-drag over the 3D view.
        driver.move_pixel(round(view_x), round(view_y))
        driver.button_down(3)
        for step in range(1, 13):
            driver.move_pixel(round(view_x + step * 12), round(view_y - step * 4))
        driver.button_up(3)
        time.sleep(0.8)
        capture(driver, args.output / "2-orbited.png")
        # Each camera preset (J cycles through those given with --camera) in
        # turn.
        from Xlib import XK
        from Xlib.ext import xtest

        def control_key(name: str) -> None:
            control = driver.display.keysym_to_keycode(XK.string_to_keysym("Control_L"))
            code = driver.display.keysym_to_keycode(XK.string_to_keysym(name))
            # Held long enough for the editor, which polls key state once a
            # frame, to see both keys down.
            xtest.fake_input(driver.display, X.KeyPress, control)
            driver.display.sync()
            time.sleep(0.08)
            xtest.fake_input(driver.display, X.KeyPress, code)
            driver.display.sync()
            time.sleep(0.12)
            xtest.fake_input(driver.display, X.KeyRelease, code)
            driver.display.sync()
            time.sleep(0.08)
            xtest.fake_input(driver.display, X.KeyRelease, control)
            driver.display.sync()
            time.sleep(0.5)

        if args.edges:
            control_key("2")
        for shot, label in enumerate(args.labels, start=3):
            driver.key("j")
            time.sleep(1.5)
            capture(driver, args.output / f"{shot}-{label}.png")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    main()

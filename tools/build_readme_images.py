#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Make the README images in docs/images/readme/ from the running editor.

Each image is a scene: the editor is started on a private X server (Xvfb)
with a model from this repository and its automation API on, the view is
set up with real pointer clicks sent through XTEST, and the window is
captured. The images are reduced to a palette so each stays under the
150 kB of the OpenAEC README standard.

    python3 tools/build_readme_images.py                 # all scenes
    python3 tools/build_readme_images.py hero steel-3d   # some scenes
    python3 tools/build_readme_images.py --check         # verify only

The editor binary is $BIM_BUILD_DIR/open-bim-studio-dev (build it with
`bash ./build.sh dev`), or the one given with --binary. Rendering uses
Mesa's software Vulkan driver (lavapipe) unless --vulkan-icd says otherwise,
so no GPU is needed. Requires Xvfb, libX11, libXtst and Pillow; it compiles
nothing.

`--check` fails when a README links an image that is missing, when an image
in docs/images/readme/ is used by neither README, or when one exceeds
150 kB.

The clicks are window pixels of the editor's 1440 x 900 default layout.
When the layout changes, check the images and adjust the coordinates below.
"""
from __future__ import annotations

import argparse
import ctypes
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs" / "images" / "readme"
READMES = (ROOT / "README.md", ROOT / "README.nl.md")
LIMIT = 150 * 1024
DISPLAY = ":97"

sys.path.insert(0, str(ROOT / "automation" / "mcp"))

# name: (editor arguments, steps). An argument ending in .bim is a model in
# this repository. A step is ("click", x, y), ("fit",) or ("wait", seconds).
SCENES = {
    "hero": (["--example"], [("click", 253, 166), ("wait", 4)]),
    "plan": (["--example"], [("wait", 2)]),
    "elevation": (["--example"], [("click", 26, 190), ("wait", 1), ("click", 120, 374), ("wait", 3)]),
    "steel-3d": (["tests/models/steel-connection-hall.bim"], [("click", 202, 166), ("wait", 4)]),
    "reinforcement": (["tests/models/reinforcement-details.bim"], [("fit",), ("wait", 3)]),
    "schedule": (["--example"], [("click", 26, 190), ("wait", 1), ("click", 80, 454), ("wait", 1), ("click", 130, 474), ("wait", 3)]),
}


def openable(model: Path, folder: Path) -> Path:
    """The model, or a copy with a window and a door type when it has none.

    The editor opens a .bim file only when it holds a window type and a door
    type; the reinforcement review models in tests/models/ have neither.
    """
    lines = model.read_text(encoding="utf-8").splitlines()
    if any(line.startswith("openingtype ") for line in lines):
        return model
    following = next(int(line.split()[1]) for line in lines if line.startswith("next "))
    types = [f"openingtype {following} 1.2 1.5 0.9 0.05 0 Window 1200x1500",
             f"openingtype {following + 1} 0.9 2.1 0 0.05 1 Door 900x2100"]
    first_wall = next((i for i, line in enumerate(lines) if line.startswith("wall ")), len(lines))
    lines[first_wall:first_wall] = types
    lines = [f"next {following + 2}" if line.startswith("next ") else line for line in lines]
    copy = folder / model.name
    copy.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return copy


class Pointer:
    """Pointer clicks on an X display through the XTEST extension."""

    def __init__(self, display: str):
        self.x11 = ctypes.CDLL("libX11.so.6")
        self.xtst = ctypes.CDLL("libXtst.so.6")
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x11.XFlush.argtypes = [ctypes.c_void_p]
        self.x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
        self.xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
        self.display = self.x11.XOpenDisplay(display.encode())
        if not self.display:
            raise SystemExit(f"cannot open X display {display}")

    def click(self, x: int, y: int) -> None:
        self.xtst.XTestFakeMotionEvent(self.display, -1, x, y, 0)
        self.x11.XFlush(self.display)
        time.sleep(0.2)
        for pressed in (1, 0):
            self.xtst.XTestFakeButtonEvent(self.display, 1, pressed, 0)
            self.x11.XFlush(self.display)
            time.sleep(0.1)

    def close(self) -> None:
        self.x11.XCloseDisplay(self.display)


def wait_for_api(folder: Path, process: subprocess.Popen, seconds: float = 60.0):
    import open_bim_studio_mcp as mcp
    modeller = mcp.Modeller()
    deadline = time.time() + seconds
    while True:
        if process.poll() is not None:
            raise SystemExit(f"the editor stopped with code {process.returncode}")
        try:
            modeller.connect(str(folder))
            modeller.request("state", timeout=5.0)
            return modeller
        except Exception:
            if time.time() > deadline:
                raise SystemExit("the editor's automation API did not answer")
            time.sleep(1.0)


def capture(path: Path) -> None:
    from PIL import ImageGrab
    image = ImageGrab.grab(xdisplay=DISPLAY)
    image = image.crop(image.getbbox())
    image = image.convert("RGB").quantize(colors=256, dither=0)
    image.save(path, optimize=True)
    size = path.stat().st_size
    print(f"{path.relative_to(ROOT)}: {image.width} x {image.height}, {size // 1024} kB")
    if size > LIMIT:
        raise SystemExit(f"{path.name} is larger than {LIMIT // 1024} kB")


def make(scene: str, binary: Path, icd: str) -> None:
    arguments, steps = SCENES[scene]
    with tempfile.TemporaryDirectory() as temporary:
        api = Path(temporary) / "api"
        arguments = [str(openable(ROOT / a, Path(temporary))) if a.endswith(".bim") else a for a in arguments]
        environment = {k: v for k, v in os.environ.items() if k != "WAYLAND_DISPLAY"}
        environment.update(DISPLAY=DISPLAY, XDG_SESSION_TYPE="x11", VK_ICD_FILENAMES=icd)
        editor = subprocess.Popen([str(binary), *arguments, "--api", str(api)], cwd=ROOT, env=environment,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            modeller = wait_for_api(api, editor)
            time.sleep(3.0)
            pointer = Pointer(DISPLAY)
            for step in steps:
                if step[0] == "click":
                    pointer.click(step[1], step[2])
                elif step[0] == "fit":
                    modeller.request("fit")
                elif step[0] == "wait":
                    time.sleep(step[1])
            pointer.close()
            capture(IMAGES / f"{scene}.png")
        finally:
            editor.terminate()
            try:
                editor.wait(10)
            except subprocess.TimeoutExpired:
                editor.kill()


def check() -> int:
    problems = []
    used = set()
    for readme in READMES:
        if not readme.exists():
            problems.append(f"{readme.name} is missing")
            continue
        for link in re.findall(r"docs/images/readme/([\w.-]+)", readme.read_text(encoding="utf-8")):
            used.add(link)
            if not (IMAGES / link).exists():
                problems.append(f"{readme.name} links docs/images/readme/{link}, which does not exist")
    for image in sorted(IMAGES.glob("*")):
        if image.name not in used:
            problems.append(f"docs/images/readme/{image.name} is used by neither README")
        if image.stat().st_size > LIMIT:
            problems.append(f"docs/images/readme/{image.name} is larger than {LIMIT // 1024} kB")
    for problem in problems:
        print(problem)
    if not problems:
        print(f"README images: {len(used)} linked, all present and under {LIMIT // 1024} kB")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("scenes", nargs="*", help=f"scenes to make (default: all of {', '.join(SCENES)})")
    parser.add_argument("--check", action="store_true", help="only verify the images and the README links")
    parser.add_argument("--binary", type=Path, help="editor binary (default: $BIM_BUILD_DIR/open-bim-studio-dev)")
    parser.add_argument("--vulkan-icd", default="/usr/share/vulkan/icd.d/lvp_icd.json",
                        help="Vulkan driver manifest (default: Mesa lavapipe)")
    arguments = parser.parse_args()
    if arguments.check:
        return check()
    unknown = [scene for scene in arguments.scenes if scene not in SCENES]
    if unknown:
        parser.error(f"unknown scene {', '.join(unknown)}; the scenes are {', '.join(SCENES)}")
    binary = arguments.binary or Path(os.environ.get("BIM_BUILD_DIR", ROOT / "build")) / "open-bim-studio-dev"
    if not binary.exists():
        raise SystemExit(f"no editor at {binary}; build it with `bash ./build.sh dev` or pass --binary")
    IMAGES.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24", "-nolisten", "tcp"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1.0)
        for scene in arguments.scenes or SCENES:
            make(scene, binary.resolve(), arguments.vulkan_icd)
    finally:
        server.terminate()
        server.wait(10)
    return check()


if __name__ == "__main__":
    sys.exit(main())

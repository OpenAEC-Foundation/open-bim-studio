#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""MCP server for Open BIM Studio: an AI assistant drives the modeller.

The modeller serves its automation API (`bim_api.dl`) through a folder: this
server publishes UTF-8 requests and reads JSON responses under an OS-owned
transport lock. MCP uses newline-delimited JSON-RPC 2.0 over stdio. Windows
capture/input needs only the Python standard library; Linux screenshots need
python-xlib and Pillow.

Two ways to reach a modeller:

- `launch` opens a visible native Windows app, or a nested Linux X server
  (Xephyr). Override the binary with OPEN_BIM_STUDIO_BINARY.
- `connect` attaches to a modeller someone started with `--api FOLDER`, or
  in which Collaborate > Automation > API / MCP was switched on (the folder
  is then `open-bim-studio-api` in the directory the modeller runs in).
- `--api-folder FOLDER` or OPEN_BIM_STUDIO_API_FOLDER configures that folder
  at startup without a separate connect call; `--pid` selects the Windows app.

Register it with an MCP client, for example in Claude Code:

    claude mcp add open-bim-studio -- python3 /path/to/open_bim_studio_mcp.py
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from contextvars import ContextVar
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "open-bim-studio", "version": "0.1.0"}
WINDOW_NAMES = ("Open BIM Studio", "BIM slice")


@contextmanager
def folder_transaction(folder: Path, timeout: float):
    """OS-owned lock shared by HTTP/MCP processes; automatically released on exit/crash."""
    with (folder / "transport.lock").open("a+b") as lock:
        if lock.seek(0, os.SEEK_END) == 0:
            lock.write(b"\0")
            lock.flush()
        deadline = time.monotonic() + timeout
        if sys.platform == "win32":
            import msvcrt

            def acquire():
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)

            def release():
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            def acquire():
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            def release():
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        while True:
            try:
                acquire()
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise ToolError("another API client is busy; no turn at the native request slot")
                time.sleep(.02)
        try:
            yield
        finally:
            release()


class Modeller:
    """The modeller this server drives: its API folder, its display and,
    when this server started it, its processes."""

    def __init__(self) -> None:
        self.folder: Path | None = None
        self.display: str | None = os.environ.get("DISPLAY")
        self.processes: list[subprocess.Popen] = []
        self.modeller: subprocess.Popen | None = None
        self.log: Path | None = None
        self.counter = 0
        self.pid: int | None = None
        self.binary: str | None = None
        self.ui = None
        self.request_lock = threading.RLock()

    # -- reaching it ---------------------------------------------------
    def connect(self, folder: str, display: str | None = None, pid: int | None = None) -> dict:
        path = Path(folder).expanduser().resolve()
        if not path.is_dir():
            raise ToolError(f"no API folder at {path}: start the modeller with --api {path}, "
                            "or switch on Collaborate > Automation > API / MCP")
        if self.modeller is not None and self.modeller.poll() is None and path != self.folder:
            raise ToolError("close the modeller this server launched before connecting to another API folder")
        self.folder = path
        if self.modeller is None:
            self.pid, self.binary, self.ui = pid, None, None
        if display:
            self.display = display
        return self.request("ping")

    def launch(self, binary: str | None, display: str | None, example: bool,
               width: int, height: int) -> dict:
        binary = binary or os.environ.get("OPEN_BIM_STUDIO_BINARY") or shutil.which("open-bim-studio")
        if not binary or not Path(binary).expanduser().exists():
            raise ToolError("no modeller binary: give `binary` or set OPEN_BIM_STUDIO_BINARY")
        # The modeller runs in a folder of its own, so a relative path is made absolute here.
        binary = str(Path(binary).expanduser().resolve())
        if self.modeller is not None and self.modeller.poll() is None:
            raise ToolError("this server already launched a modeller; close it before launching another")
        self.close()
        windows = sys.platform == "win32"
        display = None if windows else display or os.environ.get("OPEN_BIM_STUDIO_DISPLAY") or ":97"
        work = Path(tempfile.mkdtemp(prefix="open-bim-studio-mcp-"))
        folder = work / "api"
        folder.mkdir()
        if not windows and not Path(f"/tmp/.X11-unix/X{display.lstrip(':')}").exists():
            if not shutil.which("Xephyr"):
                raise ToolError("Xephyr is not installed; give the display of a running X server")
            self.processes.append(subprocess.Popen(
                ["Xephyr", display, "-screen", f"{width}x{height}", "-ac", "-br", "-noreset"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            time.sleep(1.5)
        environment = dict(os.environ)
        if not windows:
            environment["DISPLAY"] = display
        elif not environment.get("OPEN_BIM_STUDIO_HOME"):
            home = Path(binary).parent
            if (home / "fonts").is_dir() and (home / "shaders").is_dir():
                environment["OPEN_BIM_STUDIO_HOME"] = str(home)
        arguments = [binary] + (["--example"] if example else []) + ["--api", str(folder)]
        # The modeller's output goes to a log, to say why it stopped.
        self.log = work / "modeller.log"
        with open(self.log, "wb") as log:
            self.modeller = subprocess.Popen(arguments, cwd=str(Path(binary).parent if windows else work), env=environment,
                                             stdout=log, stderr=subprocess.STDOUT,
                                             creationflags=0x08000000 if windows else 0)
        self.processes.append(self.modeller)
        self.folder = folder
        self.display = display
        self.pid, self.binary, self.ui = self.modeller.pid, binary, None
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                return self.request("ping", timeout=2.0)
            except ToolError:
                self.check_running()
                time.sleep(0.5)
        raise ToolError(f"the modeller started but its API did not answer within 60 s (log: {self.log})")

    def check_running(self) -> None:
        """Fails at once when the modeller this server launched has stopped."""
        if self.modeller is None or self.modeller.poll() is None:
            return
        tail = ""
        if self.log is not None and self.log.exists():
            lines = self.log.read_text(encoding="utf-8", errors="replace").splitlines()
            tail = "\n".join(line for line in lines[-8:] if "DRI3" not in line)
        message = f"the modeller stopped (exit code {self.modeller.returncode})"
        if tail:
            message += ":\n" + tail
        if "shader" in tail or "font" in tail:
            message += ("\nA modeller built in a tree finds its fonts and shaders through "
                        "OPEN_BIM_STUDIO_HOME (fonts/, shaders/).")
        raise ToolError(message)

    def close(self) -> None:
        for process in reversed(self.processes):
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        self.processes.clear()
        self.modeller = None
        self.folder, self.pid, self.binary, self.ui = None, None, None, None

    # -- the API ---------------------------------------------------------
    def request(self, verb: str, *arguments: object, timeout: float = 15.0) -> dict:
        with self.request_lock:
            if self.folder is None:
                raise ToolError("not connected: call `launch` or `connect` first")
            with folder_transaction(self.folder, timeout):
                return self._request(verb, *arguments, timeout=timeout)

    def _request(self, verb: str, *arguments: object, timeout: float = 15.0) -> dict:
        if self.folder is None:
            raise ToolError("not connected: call `launch` or `connect` first")
        self.counter += 1
        request_id = f"{os.getpid()}-{self.counter}"
        lines = [request_id, verb] + [str(argument) for argument in arguments]
        if any("\n" in line or "\r" in line for line in lines):
            raise ToolError("API arguments must each be a single line")
        response = self.folder / "response"
        if response.exists():
            response.unlink()
        temporary = self.folder / "request.tmp"
        temporary.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
        os.replace(temporary, self.folder / "request")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.check_running()
            if response.exists():
                text = response.read_text(encoding="utf-8")
                first, _, body = text.partition("\n")
                if first.strip() == request_id:
                    response.unlink()
                    answer = json.loads(body)
                    if not answer.get("ok", False):
                        raise ToolError(answer.get("error", "the modeller refused"))
                    return answer
                # A previous timed-out request may still finish. Consume its stale
                # answer so Windows rename can publish the response we are awaiting.
                response.unlink(missing_ok=True)
            time.sleep(0.02)
        raise ToolError(f"no answer to '{verb}' within {timeout:.0f} s (is the modeller running?)")

    # -- the screen --------------------------------------------------------
    def window(self, pid: int | None = None):
        if sys.platform != "win32":
            raise ToolError("native UI control is supported on Windows; use model API tools on other platforms")
        if self.pid is not None and self.modeller is not None and pid not in (None, self.pid):
            raise ToolError("UI is bound to the modeller this server launched")
        from windows_ui import WindowsUI
        if self.ui is None:
            self.ui = WindowsUI(self.pid, self.binary)
        self.ui.bind(pid)
        return self.ui

    def screenshot(self, whole_screen: bool) -> bytes:
        if sys.platform == "win32":
            if whole_screen:
                raise ToolError("Windows screenshots are restricted to the bound app client area")
            return self.window().screenshot()
        try:
            from Xlib import X, display as xdisplay
            from PIL import Image
        except ImportError as missing:
            raise ToolError(f"screenshots need python-xlib and Pillow ({missing})")
        connection = xdisplay.Display(self.display)
        root = connection.screen().root
        target = root
        if not whole_screen:
            found = find_window(root)
            if found is None:
                connection.close()
                raise ToolError("no modeller window on the selected X display")
            target = found
        geometry = target.get_geometry()
        raw = target.get_image(0, 0, geometry.width, geometry.height, X.ZPixmap, 0xFFFFFFFF)
        image = Image.frombytes("RGB", (geometry.width, geometry.height), raw.data, "raw", "BGRX")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        connection.close()
        return buffer.getvalue()


def find_window(root):
    pending = [root]
    while pending:
        window = pending.pop()
        try:
            name = window.get_wm_name()
        except Exception:
            name = None
        if name and any(wanted in str(name) for wanted in WINDOW_NAMES):
            return window
        try:
            pending.extend(window.query_tree().children)
        except Exception:
            pass
    return None


class ToolError(Exception):
    pass


MODELLER = Modeller()
ACTIVE_MODELLER = ContextVar("open_bim_studio_modeller", default=None)


def current_modeller():
    return ACTIVE_MODELLER.get() or MODELLER


def number(value: object, name: str) -> float:
    try:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError()
        return result
    except (TypeError, ValueError):
        raise ToolError(f"`{name}` must be a number")


def text_result(payload: object) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=1)}]}


# The tools: name -> (description, input schema, handler).
POINT = {"type": "number", "description": "metres, in the plan"}
TOOLS: dict[str, tuple[str, dict, object]] = {}


def tool(name: str, description: str, properties: dict | None = None, required: list[str] | None = None):
    def register(handler):
        schema = {"type": "object", "properties": properties or {}}
        if required:
            schema["required"] = required
        TOOLS[name] = (description, schema, handler)
        return handler
    return register


@tool("launch", "Start the modeller with its automation API on and connect to it. Windows opens a visible "
      "native app window; Linux uses a nested X server (Xephyr). A modeller not installed finds its fonts "
      "and shaders through the environment variable OPEN_BIM_STUDIO_HOME.",
      {"binary": {"type": "string", "description": "path to the modeller (default: OPEN_BIM_STUDIO_BINARY or open-bim-studio on PATH)"},
       "display": {"type": "string", "description": "X display, default :97"},
       "example": {"type": "boolean", "description": "open the example house (default true)"},
       "width": {"type": "integer", "description": "Linux nested display width"},
       "height": {"type": "integer", "description": "Linux nested display height"}})
def launch_tool(arguments: dict) -> dict:
    answer = current_modeller().launch(arguments.get("binary"), arguments.get("display"),
                             arguments.get("example", True), int(arguments.get("width", 1600)),
                             int(arguments.get("height", 1000)))
    return text_result({"connected": str(current_modeller().folder), "display": current_modeller().display, **answer})


@tool("connect", "Attach to a running modeller started with --api FOLDER (or with Collaborate > Automation > "
       "API / MCP switched on: FOLDER is open-bim-studio-api where it runs).",
      {"folder": {"type": "string"}, "display": {"type": "string", "description": "its Linux X display"},
       "pid": {"type": "integer", "description": "Windows app process id; required if multiple app windows exist"}},
      ["folder"])
def connect_tool(arguments: dict) -> dict:
    return text_result(current_modeller().connect(arguments["folder"], arguments.get("display"), arguments.get("pid")))


@tool("close", "Close the modeller (and its X server) this server launched.")
def close_tool(arguments: dict) -> dict:
    current_modeller().close()
    return text_result({"closed": True})


@tool("screenshot", "PNG of the app. Windows captures physical client pixels of its visible foreground window "
      "(including Vulkan), restores/focuses it and refuses an offscreen/covered window. Linux uses X11.",
      {"whole_screen": {"type": "boolean"}, "save_to": {"type": "string", "description": "also save the PNG here"}})
def screenshot_tool(arguments: dict) -> dict:
    png = current_modeller().screenshot(bool(arguments.get("whole_screen", False)))
    if arguments.get("save_to"):
        Path(arguments["save_to"]).expanduser().write_bytes(png)
    return {"content": [{"type": "image", "data": base64.b64encode(png).decode("ascii"), "mimeType": "image/png"}]}


@tool("ui_window", "Bind/inspect the native Windows app window. Refuses ambiguous windows; supply pid to choose. "
      "Returns screenshot/client pixel dimensions. UI tools focus this window and never target another process.",
      {"pid": {"type": "integer"}})
def ui_window_tool(arguments: dict) -> dict:
    return text_result(current_modeller().window(arguments.get("pid")).info())


PIXEL = {"type": "integer", "description": "physical pixel relative to top left of app screenshot/client area"}


@tool("ui_click", "Click a visible UI control in the bound Windows app using screenshot/client pixels. "
      "Coordinates outside its client area and covered points are refused. Holds down 80 ms for native frame polling. "
      "For background model edits use click/create_*.",
      {"x": PIXEL, "y": PIXEL, "button": {"type": "string", "enum": ["left", "right", "middle"]},
       "count": {"type": "integer", "enum": [1, 2]}}, ["x", "y"])
def ui_click_tool(arguments: dict) -> dict:
    return text_result(current_modeller().window().click(arguments["x"], arguments["y"],
                       arguments.get("button", "left"), arguments.get("count", 1)))


@tool("ui_move", "Move the pointer for hover/snapping inside the bound Windows app, without clicking. "
      "Coordinates are screenshot/client pixels; refuses covered points and externally held mouse buttons.",
      {"x": PIXEL, "y": PIXEL}, ["x", "y"])
def ui_move_tool(arguments: dict) -> dict:
    return text_result(current_modeller().window().move(arguments["x"], arguments["y"]))


@tool("ui_drag", "Drag in the bound Windows app for box selection, pan or gizmos, using screenshot/client pixels. "
      "Validates both endpoints and path before pressing; releases the button on errors. Focus loss, movement "
      "or resize aborts the drag. No modifiers are injected; release physical modifiers/buttons first. "
      "steps defaults 12 (1..120); duration_ms defaults 180 (0..2000), plus an 80 ms initial hold.",
      {"from_x": PIXEL, "from_y": PIXEL, "to_x": PIXEL, "to_y": PIXEL,
       "button": {"type": "string", "enum": ["left", "middle", "right"]},
       "steps": {"type": "integer", "minimum": 1, "maximum": 120},
       "duration_ms": {"type": "integer", "minimum": 0, "maximum": 2000}},
      ["from_x", "from_y", "to_x", "to_y"])
def ui_drag_tool(arguments: dict) -> dict:
    return text_result(current_modeller().window().drag(arguments["from_x"], arguments["from_y"],
                       arguments["to_x"], arguments["to_y"], arguments.get("button", "left"),
                       arguments.get("steps", 12), arguments.get("duration_ms", 180)))


@tool("ui_key", "Press a key/chord in the bound Windows app, e.g. escape, enter, ctrl+z, shift+tab. "
      "Holds the chord 80 ms for native frame polling, then releases all keys. Focus is checked throughout. "
      "Desktop switching/system shortcuts are refused.",
      {"key": {"type": "string"}}, ["key"])
def ui_key_tool(arguments: dict) -> dict:
    return text_result(current_modeller().window().key(arguments["key"]))


@tool("ui_type", "Type Unicode text into the focused control of the bound Windows app. "
      "Use ui_click to focus a field, ui_type for its text, and ui_key for enter/tab.",
      {"text": {"type": "string"}}, ["text"])
def ui_type_tool(arguments: dict) -> dict:
    return text_result(current_modeller().window().type_text(arguments["text"]))


@tool("ui_scroll", "Scroll at client pixel x,y in the bound Windows app. Positive steps scroll up; negative down. "
      "One step is one Windows wheel notch; at most 100 per call.",
      {"x": PIXEL, "y": PIXEL, "steps": {"type": "integer"}}, ["x", "y", "steps"])
def ui_scroll_tool(arguments: dict) -> dict:
    return text_result(current_modeller().window().scroll(arguments["x"], arguments["y"], arguments["steps"]))


@tool("state", "The editor's state: tool, selection, message, active storey, element counts, undo steps.")
def state_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("state"))


@tool("elements", "The model's storeys, walls, slabs, building systems and openings with ids and geometry.")
def elements_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("elements"))


@tool("buttons", "Every ribbon button (tab, group, label, command-line key, command code); press one with `press_button`.")
def buttons_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("buttons"))


@tool("press_button", "Press the ribbon button whose label starts with `label` (e.g. 'Wall', 'Floor', "
      "'Building system', 'Align'), as a click on it would: the window runs it on its next frame, so the "
      "window's own commands (Tile, Export, panels) work too. 'Tab/Label' picks a label several tabs share "
      "('View/Detail', 'Sketch/Delete'). Returns the state after the press.",
      {"label": {"type": "string"}}, ["label"])
def press_button_tool(arguments: dict) -> dict:
    modeller = current_modeller()
    pressed = modeller.request("ribbon", arguments["label"])
    if not pressed.get("ok", False):
        return text_result(pressed)
    time.sleep(0.25)
    state = modeller.request("state")
    state["pressed"] = pressed.get("pressed")
    return text_result(state)


@tool("key", "Type a key or command code (as the keyboard would: 87 W, 256 Esc, 258 Tab, 257 Enter, 90 undo). "
      "Esc cancels what is under way and clears the selection; the tool returns to Select.",
      {"code": {"type": "integer"}}, ["code"])
def key_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("key", int(arguments["code"])))


@tool("click", "Click at plan point x, y (metres) with the active tool, as the mouse would.",
      {"x": POINT, "y": POINT}, ["x", "y"])
def click_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("click", number(arguments["x"], "x"), number(arguments["y"], "y")))


@tool("move_pointer", "Move the pointer to plan point x, y (metres) without clicking (previews, snaps).",
      {"x": POINT, "y": POINT}, ["x", "y"])
def pointer_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("pointer", number(arguments["x"], "x"), number(arguments["y"], "y")))


@tool("select", "Select element `id` (from `elements`).", {"id": {"type": "integer"}}, ["id"])
def select_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("select", int(arguments["id"])))


@tool("properties", "The selection's properties panel rows: label, value and the code to set it (0: read only, "
      "-1: a heading).")
def properties_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("properties"))


@tool("set_property", "Type `value` into property `code` of the selection (as typing in the properties panel; "
      "a 'click' property takes no value). Lengths are in the project's length unit, as the panel shows "
      "them (millimetres by default: a 2.8 m height is 2800).",
      {"code": {"type": "integer"}, "value": {"type": "string"}}, ["code"])
def set_property_tool(arguments: dict) -> dict:
    code = int(arguments["code"])
    rows = current_modeller().request("properties").get("rows", [])
    if not any(int(row.get("code", 0)) == code for row in rows if int(row.get("code", 0)) > 0):
        raise ToolError(f"the selection has no property with code {code} (see `properties`)")
    extra = [arguments["value"]] if arguments.get("value") not in (None, "") else []
    return text_result(current_modeller().request("property", code, *extra))


def rectangle_arguments(arguments: dict) -> list[float]:
    return [number(arguments[key], key) for key in ("x1", "y1", "x2", "y2")]


RECTANGLE = {"x1": POINT, "y1": POINT, "x2": POINT, "y2": POINT}


@tool("create_wall", "A wall of the current wall type on the active storey from (x1, y1) to (x2, y2).",
      RECTANGLE, ["x1", "y1", "x2", "y2"])
def wall_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("wall", *rectangle_arguments(arguments)))


@tool("create_floor", "A floor slab over the rectangle (x1, y1)-(x2, y2) on the active storey.",
      RECTANGLE, ["x1", "y1", "x2", "y2"])
def slab_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("slab", *rectangle_arguments(arguments)))


@tool("create_building_system", "A building system (curtain wall, masonry, timber frame, ...) along "
      "(x1, y1)-(x2, y2), the storey's height, of type `type_index` (see `system_types`).",
      dict(RECTANGLE, type_index={"type": "integer"}), ["x1", "y1", "x2", "y2"])
def system_tool(arguments: dict) -> dict:
    values = rectangle_arguments(arguments)
    if arguments.get("type_index") is not None:
        values.append(int(arguments["type_index"]))
    return text_result(current_modeller().request("system", *values))


@tool("system_types", "The building system types of the library (index, name, group).")
def system_types_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("systemtypes"))


TYPE_TAB = {"type": "integer", "enum": list(range(9)),
            "description": "0 Wall, 1 Slab, 2 Roof, 3 Ceiling, 4 Column, 5 Beam, 6 Pile, 7 Opening, 8 Profiles"}
TYPE_ID = {"type": "integer", "description": "stable native type id returned by list_types/create_type"}


@tool("list_types", "Read the native IfcTypes library without placing instances. Optional tab filters the library; "
      "returns stable ids, IFC type classes, material, metre dimensions, layers and usage counts. "
      "Classification strings and project lengthUnit are included. Profiles also appear in their role tab.",
      {"tab": TYPE_TAB})
def list_types_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("types", *([arguments["tab"]] if "tab" in arguments else [])))


@tool("create_type", "Add an unused native type with editable defaults; returns id. No model instance is created. "
      "Profiles tab creates a plain Beam type; use its Beam tab (5) to edit it.", {"tab": TYPE_TAB}, ["tab"])
def create_type_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("typeadd", arguments["tab"]))


@tool("duplicate_type", "Duplicate a type's definition, layers, properties and classifications. Returns a new stable id; "
      "creates no occurrence. The source id must belong to tab.", {"tab": TYPE_TAB, "id": TYPE_ID}, ["tab", "id"])
def duplicate_type_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("typeduplicate", arguments["tab"], arguments["id"]))


@tool("set_type_field", "Edit an IfcTypes field directly by id, without selecting or placing an instance. "
      "Fields: 0 name, 1 material, 2 width or layer thickness, 3 depth or opening height, 4 opening sill, "
      "5 NL-SfB, 6 OmniClass. Numeric lengths use PROJECT units (lengthUnit 0 mm, 1 cm, 2 m); "
      "list_types dimensions are metres. layer is zero-based, defaults 0, and applies to planar types. "
      "Unsupported fields, invalid dimensions and stale ids are refused atomically.",
      {"tab": TYPE_TAB, "id": TYPE_ID, "field": {"type": "integer", "enum": list(range(7))},
       "value": {"type": "string"}, "layer": {"type": "integer", "description": "zero-based layer index, default 0"}},
      ["tab", "id", "field", "value"])
def set_type_field_tool(arguments: dict) -> dict:
    extra = [arguments["layer"]] if "layer" in arguments else []
    return text_result(current_modeller().request("typeset", arguments["tab"], arguments["id"],
                       arguments["field"], arguments["value"], *extra))


@tool("apply_type", "Set the type as drawing default and apply it to the compatible current selection, "
      "as in the IfcTypes manager. An incompatible selection is retained; no occurrence is created.",
      {"tab": TYPE_TAB, "id": TYPE_ID}, ["tab", "id"])
def apply_type_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("typeapply", arguments["tab"], arguments["id"]))


@tool("delete_type", "Delete an unused native type by stable id. Refuses types referenced by model occurrences "
      "or assemblies; a successful deletion is undoable.", {"tab": TYPE_TAB, "id": TYPE_ID}, ["tab", "id"])
def delete_type_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("typedelete", arguments["tab"], arguments["id"]))


@tool("tool_options", "Read active tool, numeric input, project lengthUnit, orthoOn/orthoHeld, modify options "
      "(count/radial/sweep/copyMode/factor/radius/chamfer/axis) and snap label/point. Does not mutate model or tool state.")
def tool_options_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("options"))


@tool("create_grid", "Create a named grid line from (x1,y1) to (x2,y2), with vertical extents low/high. "
      "All coordinates are metres; returns its element id. Runs through the native model API without UI focus.",
      dict(RECTANGLE, name={"type": "string"}, low={"type": "number"}, high={"type": "number"}),
      ["name", "x1", "y1", "x2", "y2", "low", "high"])
def grid_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("grid", arguments["name"], *rectangle_arguments(arguments),
                       number(arguments["low"], "low"), number(arguments["high"], "high")))


@tool("repeat_grid", "Repeat a grid by spacing pattern, e.g. '5000 3000 3x5400'. "
      "source is its numeric element id as a string or 'selected'. Optional unit_code: 0 mm, 1 cm, 2 m; "
      "otherwise the project length unit. Returns count/ids; one native undo step.",
      {"source": {"type": "string"}, "pattern": {"type": "string"},
       "unit_code": {"type": "integer", "enum": [0, 1, 2]}}, ["source", "pattern"])
def repeat_grid_tool(arguments: dict) -> dict:
    extra = [arguments["unit_code"]] if "unit_code" in arguments else []
    return text_result(current_modeller().request("gridrepeat", arguments["source"], arguments["pattern"], *extra))


@tool("set_cursor", "Set the model's 3D cursor to plan x,y in metres (z=0). "
      "Background native operation; state returns cursor3D [x,y,z].", {"x": POINT, "y": POINT}, ["x", "y"])
def cursor_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("cursor", number(arguments["x"], "x"), number(arguments["y"], "y")))


@tool("undo", "Undo one step.")
def undo_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("undo"))


@tool("redo", "Redo one step.")
def redo_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("redo"))


@tool("fit_view", "Fit the views to the model.")
def fit_tool(arguments: dict) -> dict:
    return text_result(current_modeller().request("fit"))


RIBBON_TABS = ("Home", "MEP", "Sketch", "Modify", "View", "Model", "Collaborate", "Reinforcement",
               "Connections")


@tool("ribbon_tab", "Show ribbon tab `index` (0 Home, 1 MEP, 2 Sketch, 3 Modify, 4 View, 5 Model, "
      "6 Collaborate, 7 Reinforcement, 8 Connections).", {"index": {"type": "integer"}}, ["index"])
def tab_tool(arguments: dict) -> dict:
    index = int(arguments["index"])
    if not 0 <= index < len(RIBBON_TABS):
        raise ToolError(f"no ribbon tab {index}: the tabs are 0 to {len(RIBBON_TABS) - 1}")
    return text_result({**current_modeller().request("tab", index), "tab": RIBBON_TABS[index]})


# -- the protocol ----------------------------------------------------------
def handle(message: dict, modeller: Modeller | None = None) -> dict | None:
    active = modeller or MODELLER
    token = ACTIVE_MODELLER.set(active)
    try:
        with active.request_lock:
            return _handle(message)
    finally:
        ACTIVE_MODELLER.reset(token)


def _handle(message: dict) -> dict | None:
    if not isinstance(message, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "request must be an object"}}
    method = message.get("method")
    identifier = message.get("id")
    if identifier is None:
        return None  # a notification
    try:
        if method == "initialize":
            requested = message.get("params", {}).get("protocolVersion", PROTOCOL_VERSION)
            result = {"protocolVersion": requested, "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": SERVER_INFO,
                      "instructions": "Drive Open BIM Studio: call `launch` (or `connect`), look with "
                                      "`screenshot`, `state` and `elements`, act with `press_button` + `click`, "
                                      "the create_* tools, `select` + `set_property`, `undo`."}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": [{"name": name, "description": description, "inputSchema": schema}
                                for name, (description, schema, _) in TOOLS.items()]}
        elif method == "tools/call":
            params = message.get("params", {})
            if not isinstance(params, dict):
                return {"jsonrpc": "2.0", "id": identifier,
                        "error": {"code": -32602, "message": "tool params must be an object"}}
            name = params.get("name")
            if name not in TOOLS:
                return {"jsonrpc": "2.0", "id": identifier,
                        "error": {"code": -32602, "message": f"unknown tool {name}"}}
            try:
                arguments = params.get("arguments", {})
                validate_arguments(TOOLS[name][1], arguments)
                result = TOOLS[name][2](arguments)
            except (ToolError, ValueError, TypeError, KeyError, OSError) as refusal:
                result = {"content": [{"type": "text", "text": str(refusal)}], "isError": True}
        else:
            return {"jsonrpc": "2.0", "id": identifier,
                    "error": {"code": -32601, "message": f"unknown method {method}"}}
        return {"jsonrpc": "2.0", "id": identifier, "result": result}
    except Exception as failure:  # never let one request end the server
        return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32603, "message": str(failure)}}


def validate_arguments(schema: dict, arguments: dict) -> None:
    if not isinstance(arguments, dict):
        raise ToolError("tool arguments must be an object")
    for name in schema.get("required", []):
        if name not in arguments:
            raise ToolError(f"missing required argument: {name}")
    types = {"string": str, "integer": int, "number": (int, float), "boolean": bool}
    for name, value in arguments.items():
        if name not in schema["properties"]:
            raise ToolError(f"unknown argument: {name}")
        field = schema["properties"][name]
        expected = field.get("type")
        if expected in types and (not isinstance(value, types[expected]) or
                                  (isinstance(value, bool) and expected in ("integer", "number"))):
            raise ToolError(f"{name} must be {expected}")
        if "enum" in field and value not in field["enum"]:
            raise ToolError(f"invalid {name}; choose from {field['enum']}")


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(description="Open BIM Studio stdio MCP server")
    parser.add_argument("--api-folder", default=os.environ.get("OPEN_BIM_STUDIO_API_FOLDER"),
                        help="attach model tools to this API folder (or OPEN_BIM_STUDIO_API_FOLDER)")
    parser.add_argument("--pid", type=int, default=None, help="bind Windows UI to this app process")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    config = parse_arguments(argv)
    if config.api_folder:
        MODELLER.folder = Path(config.api_folder).expanduser().resolve()
    MODELLER.pid = config.pid
    # JSON-RPC and model API text use the same encoding on every platform.
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                answer = {"jsonrpc": "2.0", "id": None,
                          "error": {"code": -32700, "message": "invalid JSON"}}
            else:
                answer = handle(message)
            if answer is not None:
                sys.stdout.write(json.dumps(answer) + "\n")
                sys.stdout.flush()
    finally:
        MODELLER.close()


if __name__ == "__main__":
    main()

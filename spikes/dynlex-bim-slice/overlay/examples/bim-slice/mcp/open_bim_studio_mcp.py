#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""MCP server for Open BIM Studio: an AI assistant drives the modeller.

The modeller serves its automation API (`bim_api.dl`) through a folder: this
server writes a request there (`request.tmp`, renamed to `request`) and waits
for the answer (`response`). Screenshots are taken from the modeller's X11
display. The server speaks the Model Context Protocol over stdio
(newline-delimited JSON-RPC 2.0) and needs only the Python standard library,
plus python-xlib and Pillow for screenshots.

Two ways to reach a modeller:

- `launch` starts one in its own nested X server (Xephyr), so nothing
  touches the desktop: the binary, the display number and the folder are
  chosen by the server (override with the arguments or the environment
  variables OPEN_BIM_STUDIO_BINARY, OPEN_BIM_STUDIO_DISPLAY).
- `connect` attaches to a modeller someone started with `--api FOLDER`, or
  in which Collaborate > Automation > API / MCP was switched on (the folder
  is then `open-bim-studio-api` in the directory the modeller runs in).

Register it with an MCP client, for example in Claude Code:

    claude mcp add open-bim-studio -- python3 /path/to/open_bim_studio_mcp.py
"""
from __future__ import annotations

import base64
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "open-bim-studio", "version": "0.1.0"}
WINDOW_NAMES = ("Open BIM Studio", "BIM slice")


class Modeller:
    """The modeller this server drives: its API folder, its display and,
    when this server started it, its processes."""

    def __init__(self) -> None:
        self.folder: Path | None = None
        self.display: str | None = os.environ.get("DISPLAY")
        self.processes: list[subprocess.Popen] = []
        self.counter = 0

    # -- reaching it ---------------------------------------------------
    def connect(self, folder: str, display: str | None) -> dict:
        path = Path(folder).expanduser().resolve()
        if not path.is_dir():
            raise ToolError(f"no API folder at {path}: start the modeller with --api {path}, "
                            "or switch on Collaborate > Automation > API / MCP")
        self.folder = path
        if display:
            self.display = display
        return self.request("ping")

    def launch(self, binary: str | None, display: str | None, example: bool,
               width: int, height: int) -> dict:
        binary = binary or os.environ.get("OPEN_BIM_STUDIO_BINARY") or shutil.which("open-bim-studio")
        if not binary or not Path(binary).exists():
            raise ToolError("no modeller binary: give `binary` or set OPEN_BIM_STUDIO_BINARY")
        display = display or os.environ.get("OPEN_BIM_STUDIO_DISPLAY") or ":97"
        work = Path(tempfile.mkdtemp(prefix="open-bim-studio-mcp-"))
        folder = work / "api"
        folder.mkdir()
        if not Path(f"/tmp/.X11-unix/X{display.lstrip(':')}").exists():
            if not shutil.which("Xephyr"):
                raise ToolError("Xephyr is not installed; give the display of a running X server")
            self.processes.append(subprocess.Popen(
                ["Xephyr", display, "-screen", f"{width}x{height}", "-ac", "-br", "-noreset"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            time.sleep(1.5)
        environment = dict(os.environ, DISPLAY=display)
        arguments = [binary] + (["--example"] if example else []) + ["--api", str(folder)]
        self.processes.append(subprocess.Popen(arguments, cwd=str(work), env=environment,
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        self.folder = folder
        self.display = display
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                return self.request("ping", timeout=2.0)
            except ToolError:
                time.sleep(0.5)
        raise ToolError("the modeller started but its API did not answer within 60 s")

    def close(self) -> None:
        for process in reversed(self.processes):
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        self.processes.clear()

    # -- the API ---------------------------------------------------------
    def request(self, verb: str, *arguments: object, timeout: float = 15.0) -> dict:
        if self.folder is None:
            raise ToolError("not connected: call `launch` or `connect` first")
        self.counter += 1
        request_id = f"{os.getpid()}-{self.counter}"
        lines = [request_id, verb] + [str(argument) for argument in arguments]
        response = self.folder / "response"
        if response.exists():
            response.unlink()
        temporary = self.folder / "request.tmp"
        temporary.write_text("\n".join(lines) + "\n")
        os.replace(temporary, self.folder / "request")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if response.exists():
                text = response.read_text()
                first, _, body = text.partition("\n")
                if first.strip() == request_id:
                    response.unlink()
                    answer = json.loads(body)
                    if not answer.get("ok", False):
                        raise ToolError(answer.get("error", "the modeller refused"))
                    return answer
            time.sleep(0.02)
        raise ToolError(f"no answer to '{verb}' within {timeout:.0f} s (is the modeller running?)")

    # -- the screen --------------------------------------------------------
    def screenshot(self, whole_screen: bool) -> bytes:
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
            if found is not None:
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


def number(value: object, name: str) -> float:
    try:
        return float(value)
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


@tool("launch", "Start the modeller in its own nested X server (Xephyr) with its automation API on, "
      "and connect to it. Safe: nothing appears on the desktop.",
      {"binary": {"type": "string", "description": "path to the modeller (default: OPEN_BIM_STUDIO_BINARY or open-bim-studio on PATH)"},
       "display": {"type": "string", "description": "X display, default :97"},
       "example": {"type": "boolean", "description": "open the example house (default true)"},
       "width": {"type": "integer"}, "height": {"type": "integer"}})
def launch_tool(arguments: dict) -> dict:
    answer = MODELLER.launch(arguments.get("binary"), arguments.get("display"),
                             arguments.get("example", True), int(arguments.get("width", 1600)),
                             int(arguments.get("height", 1000)))
    return text_result({"connected": str(MODELLER.folder), "display": MODELLER.display, **answer})


@tool("connect", "Attach to a running modeller started with --api FOLDER (or with Collaborate > Automation > "
      "API / MCP switched on: FOLDER is open-bim-studio-api where it runs).",
      {"folder": {"type": "string"}, "display": {"type": "string", "description": "its X display, for screenshots"}},
      ["folder"])
def connect_tool(arguments: dict) -> dict:
    return text_result(MODELLER.connect(arguments["folder"], arguments.get("display")))


@tool("close", "Close the modeller (and its X server) this server launched.")
def close_tool(arguments: dict) -> dict:
    MODELLER.close()
    return text_result({"closed": True})


@tool("screenshot", "A PNG of the modeller's window (or the whole screen), to see what it shows.",
      {"whole_screen": {"type": "boolean"}, "save_to": {"type": "string", "description": "also save the PNG here"}})
def screenshot_tool(arguments: dict) -> dict:
    png = MODELLER.screenshot(bool(arguments.get("whole_screen", False)))
    if arguments.get("save_to"):
        Path(arguments["save_to"]).expanduser().write_bytes(png)
    return {"content": [{"type": "image", "data": base64.b64encode(png).decode("ascii"), "mimeType": "image/png"}]}


@tool("state", "The editor's state: tool, selection, message, active storey, element counts, undo steps.")
def state_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("state"))


@tool("elements", "The model's storeys, walls, slabs, building systems and openings with ids and geometry.")
def elements_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("elements"))


@tool("buttons", "Every ribbon button (tab, group, label, command code); press one with `press_button`.")
def buttons_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("buttons"))


@tool("press_button", "Press the ribbon button whose label starts with `label` (e.g. 'Wall', 'Floor', "
      "'Building system', 'Align'), as a click on it would: a tool becomes active.",
      {"label": {"type": "string"}}, ["label"])
def press_button_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("button", arguments["label"]))


@tool("key", "Type a key or command code (as the keyboard would: 87 W, 27 Esc, 258 Tab, 257 Enter, 90 undo).",
      {"code": {"type": "integer"}}, ["code"])
def key_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("key", int(arguments["code"])))


@tool("click", "Click at plan point x, y (metres) with the active tool, as the mouse would.",
      {"x": POINT, "y": POINT}, ["x", "y"])
def click_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("click", number(arguments["x"], "x"), number(arguments["y"], "y")))


@tool("move_pointer", "Move the pointer to plan point x, y (metres) without clicking (previews, snaps).",
      {"x": POINT, "y": POINT}, ["x", "y"])
def pointer_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("pointer", number(arguments["x"], "x"), number(arguments["y"], "y")))


@tool("select", "Select element `id` (from `elements`).", {"id": {"type": "integer"}}, ["id"])
def select_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("select", int(arguments["id"])))


@tool("properties", "The selection's properties panel rows: label, value and the code to set it (0: read only, "
      "-1: a heading).")
def properties_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("properties"))


@tool("set_property", "Type `value` into property `code` of the selection (as typing in the properties panel; "
      "a 'click' property takes no value).",
      {"code": {"type": "integer"}, "value": {"type": "string"}}, ["code"])
def set_property_tool(arguments: dict) -> dict:
    extra = [arguments["value"]] if arguments.get("value") not in (None, "") else []
    return text_result(MODELLER.request("property", int(arguments["code"]), *extra))


def rectangle_arguments(arguments: dict) -> list[float]:
    return [number(arguments[key], key) for key in ("x1", "y1", "x2", "y2")]


RECTANGLE = {"x1": POINT, "y1": POINT, "x2": POINT, "y2": POINT}


@tool("create_wall", "A wall of the current wall type on the active storey from (x1, y1) to (x2, y2).",
      RECTANGLE, ["x1", "y1", "x2", "y2"])
def wall_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("wall", *rectangle_arguments(arguments)))


@tool("create_floor", "A floor slab over the rectangle (x1, y1)-(x2, y2) on the active storey.",
      RECTANGLE, ["x1", "y1", "x2", "y2"])
def slab_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("slab", *rectangle_arguments(arguments)))


@tool("create_building_system", "A building system (curtain wall, masonry, timber frame, ...) along "
      "(x1, y1)-(x2, y2), the storey's height, of type `type_index` (see `system_types`).",
      dict(RECTANGLE, type_index={"type": "integer"}), ["x1", "y1", "x2", "y2"])
def system_tool(arguments: dict) -> dict:
    values = rectangle_arguments(arguments)
    if arguments.get("type_index") is not None:
        values.append(int(arguments["type_index"]))
    return text_result(MODELLER.request("system", *values))


@tool("system_types", "The building system types of the library (index, name, group).")
def system_types_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("systemtypes"))


@tool("undo", "Undo one step.")
def undo_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("undo"))


@tool("redo", "Redo one step.")
def redo_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("redo"))


@tool("fit_view", "Fit the views to the model.")
def fit_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("fit"))


@tool("ribbon_tab", "Show ribbon tab `index` (0 BIM, 1 MEP, 2 Sketch, 3 Modify, 4 Annotate, 5 View, 6 Manage, "
      "7 Collaborate, 8 Reinforcement, 9 Connections).", {"index": {"type": "integer"}}, ["index"])
def tab_tool(arguments: dict) -> dict:
    return text_result(MODELLER.request("tab", int(arguments["index"])))


# -- the protocol ----------------------------------------------------------
def handle(message: dict) -> dict | None:
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
            name = params.get("name")
            if name not in TOOLS:
                return {"jsonrpc": "2.0", "id": identifier,
                        "error": {"code": -32602, "message": f"unknown tool {name}"}}
            try:
                result = TOOLS[name][2](params.get("arguments") or {})
            except ToolError as refusal:
                result = {"content": [{"type": "text", "text": str(refusal)}], "isError": True}
        else:
            return {"jsonrpc": "2.0", "id": identifier,
                    "error": {"code": -32601, "message": f"unknown method {method}"}}
        return {"jsonrpc": "2.0", "id": identifier, "result": result}
    except Exception as failure:  # never let one request end the server
        return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32603, "message": str(failure)}}


def main() -> None:
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            answer = handle(message)
            if answer is not None:
                sys.stdout.write(json.dumps(answer) + "\n")
                sys.stdout.flush()
    finally:
        MODELLER.close()


if __name__ == "__main__":
    main()

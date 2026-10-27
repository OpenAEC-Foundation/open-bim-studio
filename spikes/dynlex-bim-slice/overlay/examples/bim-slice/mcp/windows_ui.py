# SPDX-License-Identifier: MPL-2.0
"""Window-bound Windows capture and input, using only the standard library.

Importing this module never loads Windows DLLs or operates on the desktop.
Coordinates and screenshots use physical pixels in the window's client area.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import math
from pathlib import PureWindowsPath
import struct
import sys
import time
import zlib


APP_NAMES = {"open-bim-studio.exe", "open-bim-studio-dev.exe"}


def client_point(rect, x, y):
    """Translate a checked client pixel to screen coordinates."""
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
           not math.isfinite(v) or int(v) != v for v in (x, y)):
        raise ValueError("coordinates must be finite integer client pixels")
    left, top, right, bottom = rect
    if not (0 <= x < right - left and 0 <= y < bottom - top):
        raise ValueError(f"point outside app client area ({right-left} x {bottom-top})")
    return left + int(x), top + int(y)


def overlaps(first, second):
    return max(first[0], second[0]) < min(first[2], second[2]) and max(first[1], second[1]) < min(first[3], second[3])


def choose_window(windows, pid=None, executable=None):
    candidates = []
    for item in windows:
        image = PureWindowsPath(item["executable"])
        expected = PureWindowsPath(executable) if executable else None
        if pid is not None and item["pid"] != pid:
            continue
        if expected is not None:
            if str(image).lower() != str(expected).lower():
                continue
        elif image.name.lower() not in APP_NAMES:
            continue
        if "open bim studio" not in item["title"].lower() and "bim slice" not in item["title"].lower():
            continue
        candidates.append(item)
    if not candidates:
        raise ValueError("no matching visible Open BIM Studio window; launch the app or pass its pid to connect/ui_window")
    if len(candidates) != 1:
        raise ValueError("multiple Open BIM Studio windows; pass an explicit pid to connect/ui_window")
    return candidates[0]


KEYS = {"ctrl": 0x11, "control": 0x11, "shift": 0x10, "alt": 0x12,
        "enter": 0x0D, "tab": 9, "escape": 0x1B, "esc": 0x1B, "space": 0x20,
        "backspace": 8, "delete": 0x2E, "insert": 0x2D, "home": 0x24, "end": 0x23,
        "pageup": 0x21, "pagedown": 0x22, "left": 0x25, "up": 0x26, "right": 0x27,
        "down": 0x28, **{f"f{i}": 0x6F+i for i in range(1, 13)}}


def key_codes(chord):
    if not isinstance(chord, str) or not chord:
        raise ValueError("key must be a named key or chord, such as escape or ctrl+z")
    parts = chord.lower().split("+")
    codes = []
    for part in parts:
        if part in KEYS:
            codes.append(KEYS[part])
        elif len(part) == 1 and part.isascii() and part.isalnum():
            codes.append(ord(part.upper()))
        else:
            raise ValueError(f"unsupported key: {part}")
    if len(codes) > 4 or len(set(codes)) != len(codes):
        raise ValueError("invalid key chord")
    if any(code not in (0x10, 0x11, 0x12) for code in codes[:-1]):
        raise ValueError("only modifiers may precede a key")
    if 0x12 in codes and any(code in (9, 0x1B, 0x20, 0x73) for code in codes):
        raise ValueError("desktop/window switching and closing shortcuts are not supported")
    if 0x11 in codes and 0x12 in codes and 0x2E in codes:
        raise ValueError("system shortcuts are not supported")
    if 0x11 in codes and 0x1B in codes:
        raise ValueError("system shortcuts are not supported")
    return codes


def png_from_bgra(width, height, pixels):
    if width <= 0 or height <= 0 or len(pixels) != width * height * 4:
        raise ValueError("invalid capture dimensions")
    rows = bytearray()
    stride = width * 4
    for start in range(0, len(pixels), stride):
        rows.append(0)
        row = pixels[start:start+stride]
        rgb = bytearray(width * 3)
        rgb[0::3], rgb[1::3], rgb[2::3] = row[2::4], row[1::4], row[0::4]
        rows.extend(rgb)

    def chunk(kind, content):
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content) & 0xffffffff)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", w.LONG), ("dy", w.LONG), ("mouseData", w.DWORD),
                ("dwFlags", w.DWORD), ("time", w.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", w.WORD), ("wScan", w.WORD), ("dwFlags", w.DWORD),
                ("time", w.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = [("type", w.DWORD), ("value", INPUTUNION)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", w.DWORD), ("biWidth", w.LONG), ("biHeight", w.LONG),
                ("biPlanes", w.WORD), ("biBitCount", w.WORD), ("biCompression", w.DWORD),
                ("biSizeImage", w.DWORD), ("biXPelsPerMeter", w.LONG), ("biYPelsPerMeter", w.LONG),
                ("biClrUsed", w.DWORD), ("biClrImportant", w.DWORD)]


class WindowsUI:
    def __init__(self, pid=None, executable=None):
        if sys.platform != "win32":
            raise ValueError("native UI control is currently supported on Windows only; use the model API on other platforms")
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.gdi = ctypes.WinDLL("gdi32", use_last_error=True)
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.pid, self.executable, self.bound = pid, executable, None
        self._declare()
        # One coordinate system for capture, hit-testing and input on mixed-DPI monitors.
        try:
            self.user.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except AttributeError:
            self.user.SetProcessDPIAware()

    def _declare(self):
        def function(dll, name, args, result):
            fn = getattr(dll, name)
            fn.argtypes, fn.restype = args, result
        self.callback_type = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
        for name, args, result in [
            ("EnumWindows", [self.callback_type, w.LPARAM], w.BOOL),
            ("IsWindowVisible", [w.HWND], w.BOOL), ("IsWindow", [w.HWND], w.BOOL),
            ("GetWindow", [w.HWND, w.UINT], w.HWND),
            ("GetWindowTextLengthW", [w.HWND], ctypes.c_int),
            ("GetWindowTextW", [w.HWND, w.LPWSTR, ctypes.c_int], ctypes.c_int),
            ("GetWindowThreadProcessId", [w.HWND, ctypes.POINTER(w.DWORD)], w.DWORD),
            ("GetClientRect", [w.HWND, ctypes.POINTER(w.RECT)], w.BOOL),
            ("GetWindowRect", [w.HWND, ctypes.POINTER(w.RECT)], w.BOOL),
            ("ClientToScreen", [w.HWND, ctypes.POINTER(w.POINT)], w.BOOL),
            ("GetForegroundWindow", [], w.HWND),
            ("SetForegroundWindow", [w.HWND], w.BOOL), ("IsIconic", [w.HWND], w.BOOL),
            ("ShowWindow", [w.HWND, ctypes.c_int], w.BOOL),
            ("GetAncestor", [w.HWND, w.UINT], w.HWND),
            ("WindowFromPoint", [w.POINT], w.HWND),
            ("GetSystemMetrics", [ctypes.c_int], ctypes.c_int),
            ("GetDC", [w.HWND], w.HDC), ("ReleaseDC", [w.HWND, w.HDC], ctypes.c_int),
            ("SetCursorPos", [ctypes.c_int, ctypes.c_int], w.BOOL),
            ("SendInput", [w.UINT, ctypes.POINTER(INPUT), ctypes.c_int], w.UINT),
            ("GetAsyncKeyState", [ctypes.c_int], ctypes.c_short),
        ]:
            function(self.user, name, args, result)
        for name, args, result in [
            ("CreateCompatibleDC", [w.HDC], w.HDC),
            ("CreateCompatibleBitmap", [w.HDC, ctypes.c_int, ctypes.c_int], w.HBITMAP),
            ("SelectObject", [w.HDC, w.HANDLE], w.HANDLE),
            ("DeleteObject", [w.HANDLE], w.BOOL), ("DeleteDC", [w.HDC], w.BOOL),
            ("BitBlt", [w.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                        w.HDC, ctypes.c_int, ctypes.c_int, w.DWORD], w.BOOL),
            ("GetDIBits", [w.HDC, w.HBITMAP, w.UINT, w.UINT, ctypes.c_void_p,
                           ctypes.POINTER(BITMAPINFOHEADER), w.UINT], ctypes.c_int),
        ]:
            function(self.gdi, name, args, result)
        function(self.kernel, "OpenProcess", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE)
        function(self.kernel, "QueryFullProcessImageNameW", [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)], w.BOOL)
        function(self.kernel, "GetProcessTimes", [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4, w.BOOL)
        function(self.kernel, "CloseHandle", [w.HANDLE], w.BOOL)

    def _process(self, pid):
        process = self.kernel.OpenProcess(0x1000, False, pid)
        if not process:
            raise ValueError("cannot inspect app process")
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            length = w.DWORD(len(buffer))
            if not self.kernel.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(length)):
                raise ValueError("cannot read app executable identity")
            stamps = [w.FILETIME() for _ in range(4)]
            if not self.kernel.GetProcessTimes(process, *(ctypes.byref(stamp) for stamp in stamps)):
                raise ValueError("cannot read app process identity")
            created = stamps[0].dwLowDateTime | (stamps[0].dwHighDateTime << 32)
            return buffer.value, created
        finally:
            self.kernel.CloseHandle(process)

    def _identity(self, hwnd):
        pid = w.DWORD()
        self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        image, created = self._process(pid.value)
        title = ctypes.create_unicode_buffer(self.user.GetWindowTextLengthW(hwnd) + 1)
        self.user.GetWindowTextW(hwnd, title, len(title))
        return {"hwnd": hwnd, "pid": pid.value, "executable": image, "created": created, "title": title.value}

    def bind(self, pid=None):
        if pid is not None:
            if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
                raise ValueError("pid must be a positive integer")
            self.pid, self.bound = pid, None
        if self.bound:
            if not self.user.IsWindow(self.bound["hwnd"]):
                raise ValueError("bound app window has closed; explicitly reconnect")
            now = self._identity(self.bound["hwnd"])
            if any(now[key] != self.bound[key] for key in ("pid", "executable", "created")):
                raise ValueError("bound app identity changed; explicitly reconnect")
            return self.bound
        windows = []

        @self.callback_type
        def visit(hwnd, _):
            if self.user.IsWindowVisible(hwnd) and not self.user.GetWindow(hwnd, 4):
                try:
                    windows.append(self._identity(hwnd))
                except ValueError:
                    pass
            return True

        self.user.EnumWindows(visit, 0)
        self.bound = choose_window(windows, self.pid, self.executable)
        return self.bound

    def rect(self):
        hwnd = self.bind()["hwnd"]
        rect, origin = w.RECT(), w.POINT()
        if not self.user.GetClientRect(hwnd, ctypes.byref(rect)) or not self.user.ClientToScreen(hwnd, ctypes.byref(origin)):
            raise ValueError("cannot locate app client area")
        if rect.right <= 0 or rect.bottom <= 0:
            raise ValueError("app window has no visible client area")
        return origin.x, origin.y, origin.x + rect.right, origin.y + rect.bottom

    def info(self):
        item = self.bind()
        left, top, right, bottom = self.rect()
        return {**item, "client_width": right-left, "client_height": bottom-top,
                "coordinate_space": "physical client pixels; origin at top left of screenshot"}

    def _foreground(self):
        hwnd = self.bind()["hwnd"]
        if self.user.IsIconic(hwnd):
            self.user.ShowWindow(hwnd, 9)
        if self.user.GetForegroundWindow() != hwnd:
            self.user.SetForegroundWindow(hwnd)
            time.sleep(.15)
        self._check_foreground()
        return hwnd

    def _check_foreground(self):
        if self.user.GetForegroundWindow() != self.bind()["hwnd"]:
            raise ValueError("app is not foreground; focus its main window and retry (modal dialogs must be closed)")

    def _hit(self, x, y):
        hwnd = self.user.WindowFromPoint(w.POINT(x, y))
        if self.user.GetAncestor(hwnd, 2) != self.bind()["hwnd"]:
            raise ValueError("app client area is covered by another window; uncover it and retry")

    def _uncovered(self, client_rect):
        """Refuse any other process's visible window above the app in Z order."""
        app = self.bind()
        blockers = []

        @self.callback_type
        def visit(hwnd, _):
            if hwnd == app["hwnd"]:
                return False
            if self.user.IsWindowVisible(hwnd) and not self.user.IsIconic(hwnd):
                rect, pid = w.RECT(), w.DWORD()
                self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value != app["pid"] and self.user.GetWindowRect(hwnd, ctypes.byref(rect)):
                    if overlaps(client_rect, (rect.left, rect.top, rect.right, rect.bottom)):
                        blockers.append(hwnd)
            return True

        self.user.EnumWindows(visit, 0)
        if blockers:
            raise ValueError("another window overlaps the app; uncover the entire client area and retry")

    def screenshot(self):
        self._foreground()
        left, top, right, bottom = self.rect()
        vx, vy = self.user.GetSystemMetrics(76), self.user.GetSystemMetrics(77)
        vw, vh = self.user.GetSystemMetrics(78), self.user.GetSystemMetrics(79)
        if left < vx or top < vy or right > vx+vw or bottom > vy+vh:
            raise ValueError("entire app client area must be visible on the desktop for Vulkan capture")
        self._uncovered((left, top, right, bottom))
        for x in (left, (left+right)//2, right-1):
            for y in (top, (top+bottom)//2, bottom-1):
                self._hit(x, y)
        width, height = right-left, bottom-top
        source, target, bitmap, previous = self.user.GetDC(None), None, None, None
        if not source:
            raise ValueError("cannot capture the visible desktop")
        try:
            target = self.gdi.CreateCompatibleDC(source)
            bitmap = self.gdi.CreateCompatibleBitmap(source, width, height)
            if not target or not bitmap:
                raise ValueError("cannot allocate window capture")
            previous = self.gdi.SelectObject(target, bitmap)
            self._check_foreground()
            if not self.gdi.BitBlt(target, 0, 0, width, height, source, left, top, 0x40CC0020):
                raise ValueError("visible app capture failed")
            self.gdi.SelectObject(target, previous)
            previous = None
            header = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), width, -height, 1, 32, 0, 0, 0, 0, 0, 0)
            pixels = ctypes.create_string_buffer(width * height * 4)
            if self.gdi.GetDIBits(source, bitmap, 0, height, pixels, ctypes.byref(header), 0) != height:
                raise ValueError("cannot read captured app pixels")
            self._check_foreground()
            self._uncovered((left, top, right, bottom))
            return png_from_bgra(width, height, pixels.raw)
        finally:
            if previous:
                self.gdi.SelectObject(target, previous)
            if bitmap:
                self.gdi.DeleteObject(bitmap)
            if target:
                self.gdi.DeleteDC(target)
            self.user.ReleaseDC(None, source)

    def _send(self, events):
        self._check_foreground()
        batch = (INPUT * len(events))(*events)
        if self.user.SendInput(len(batch), batch, ctypes.sizeof(INPUT)) != len(batch):
            raise ValueError("Windows rejected app input; run app and MCP with the same privilege level")

    def _pause_input(self, seconds, guard=None):
        deadline = time.monotonic() + seconds
        while True:
            self._check_foreground()
            if guard is not None:
                guard()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(remaining, .02))

    def _hold_input(self, guard=None):
        # The native editor polls pressed state each frame. An 80 ms hold
        # lets it observe at least two ordinary frames, including at 30 Hz.
        self._pause_input(.08, guard)

    def _wait_released(self):
        # Consecutive calls must also expose a released frame between presses.
        self._pause_input(.04)

    def _press_with_hold(self, down_events, up_events, guard=None):
        failed = False
        try:
            self._send(down_events)
            self._hold_input(guard)
        except BaseException:
            failed = True
            raise
        finally:
            # Cleanup contains release events only. It must work after focus
            # loss too; never refocus a different window or repeat a key-down.
            releases = (INPUT * len(up_events))(*up_events)
            try:
                if self.user.SendInput(len(releases), releases, ctypes.sizeof(INPUT)) != len(releases):
                    raise ValueError("Windows rejected input release")
            except Exception as release_error:
                if failed:
                    raise ValueError("input aborted and Windows could not release its keys or button; release them manually") from release_error
                raise
        self._wait_released()

    def _no_held_keys(self):
        if any(self.user.GetAsyncKeyState(code) & 0x8000 for code in (0x10, 0x11, 0x12, 0x5B, 0x5C)):
            raise ValueError("release physical modifier keys before automation")

    def _point(self, x, y):
        client_point(self.rect(), x, y)
        self._foreground()
        self._no_held_keys()
        screen_x, screen_y = client_point(self.rect(), x, y)
        self._hit(screen_x, screen_y)
        if not self.user.SetCursorPos(screen_x, screen_y):
            raise ValueError("cannot move pointer into app")
        self._check_foreground()
        self._hit(screen_x, screen_y)

    def _no_held_buttons(self):
        if any(self.user.GetAsyncKeyState(code) & 0x8000 for code in (1, 2, 4, 5, 6)):
            raise ValueError("release physical mouse buttons before automation")

    def move(self, x, y):
        """Move for hover/snapping without pressing a mouse button."""
        self._no_held_buttons()
        self._point(x, y)
        return self.info()

    def drag(self, from_x, from_y, to_x, to_y, button="left", steps=12, duration_ms=180):
        """Perform a bounded gesture in one fixed client rectangle.

        Focus is acquired only before the gesture. During it, focus/identity,
        geometry and occlusion changes abort rather than retargeting input.
        The finally block releases only the synthetic button this call pressed.
        """
        if button not in ("left", "right", "middle"):
            raise ValueError("button must be left/right/middle")
        if type(steps) is not int or not 1 <= steps <= 120:
            raise ValueError("steps must be an integer between 1 and 120")
        if type(duration_ms) is not int or not 0 <= duration_ms <= 2000:
            raise ValueError("duration_ms must be an integer between 0 and 2000")
        initial = self.rect()
        client_point(initial, from_x, from_y)
        client_point(initial, to_x, to_y)
        self._foreground()
        self._no_held_keys()
        self._no_held_buttons()
        rect = self.rect()
        start = client_point(rect, from_x, from_y)
        finish = client_point(rect, to_x, to_y)
        path = [(round(start[0] + (finish[0] - start[0]) * step / steps),
                 round(start[1] + (finish[1] - start[1]) * step / steps)) for step in range(steps + 1)]
        # Refuse any covered endpoint or intermediate point before mouse-down.
        for point in path:
            self._hit(*point)

        def guard():
            self._check_foreground()
            self._no_held_keys()
            if self.rect() != rect:
                raise ValueError("app moved or resized during drag; retry with a new screenshot")

        def position(point):
            guard()
            self._hit(*point)
            if not self.user.SetCursorPos(*point):
                raise ValueError("cannot move pointer into app")
            guard()
            self._hit(*point)

        position(start)
        down, up = {"left": (2, 4), "right": (8, 16), "middle": (32, 64)}[button]
        failed = False
        try:
            # Enter the cleanup region before injection, including a partial or
            # failed SendInput call. Never acquire focus again after this point.
            self._send([INPUT(type=0, mi=MOUSEINPUT(dwFlags=down))])
            # Establish the start point over multiple native frames even when
            # the requested motion duration is zero.
            self._hold_input(guard)
            started = time.monotonic()
            for step, point in enumerate(path[1:], 1):
                deadline = started + (duration_ms / 1000) * step / steps
                while True:
                    guard()
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    time.sleep(min(remaining, .02))
                position(point)
        except BaseException:
            failed = True
            raise
        finally:
            # A release must still be sent after focus loss. It contains no
            # movement/down/keyboard event and cannot start input in another app.
            release = (INPUT * 1)(INPUT(type=0, mi=MOUSEINPUT(dwFlags=up)))
            try:
                if self.user.SendInput(1, release, ctypes.sizeof(INPUT)) != 1:
                    raise ValueError("Windows rejected mouse-button release")
            except Exception as release_error:
                if failed:
                    raise ValueError("drag aborted and Windows could not release the mouse button; release it manually") from release_error
                raise
        self._wait_released()
        return self.info()

    def click(self, x, y, button="left", count=1):
        if button not in ("left", "right", "middle") or type(count) is not int or count not in (1, 2):
            raise ValueError("button must be left/right/middle and count must be 1 or 2")
        self._no_held_buttons()
        self._point(x, y)
        rect = self.rect()
        screen_point = client_point(rect, x, y)
        def guard():
            self._no_held_keys()
            if self.rect() != rect:
                raise ValueError("app moved or resized during click; retry with a new screenshot")
            self._hit(*screen_point)
        down, up = {"left": (2, 4), "right": (8, 16), "middle": (32, 64)}[button]
        for _ in range(count):
            guard()
            self._press_with_hold([INPUT(type=0, mi=MOUSEINPUT(dwFlags=down))],
                                  [INPUT(type=0, mi=MOUSEINPUT(dwFlags=up))], guard)
        return self.info()

    def key(self, chord):
        codes = key_codes(chord)
        self._foreground()
        self._no_held_keys()
        # Explicit physical E0 scan codes avoid VK-to-scan ambiguity: GLFW
        # distinguishes navigation keys from keypad keys using that prefix.
        navigation = {0x21: 0x49, 0x22: 0x51, 0x23: 0x4F, 0x24: 0x47,
                      0x25: 0x4B, 0x26: 0x48, 0x27: 0x4D, 0x28: 0x50,
                      0x2D: 0x52, 0x2E: 0x53}
        def event(code, releasing=False):
            if code in navigation:
                # SCANCODE | EXTENDEDKEY, plus KEYUP for release. wVk is
                # ignored in scan-code mode and deliberately remains zero.
                return INPUT(type=1, ki=KEYBDINPUT(wScan=navigation[code], dwFlags=11 if releasing else 9))
            return INPUT(type=1, ki=KEYBDINPUT(wVk=code, dwFlags=2 if releasing else 0))
        events = [event(code) for code in codes]
        releases = [event(code, True) for code in reversed(codes)]
        self._press_with_hold(events, releases)
        return self.info()

    def type_text(self, text):
        if not isinstance(text, str) or len(text) > 10000 or any(ord(ch) < 32 for ch in text):
            raise ValueError("text must contain at most 10000 printable characters; use ui_key for enter/tab")
        self._foreground()
        self._no_held_keys()
        encoded = text.encode("utf-16-le")
        for offset in range(0, len(encoded), 2):
            unit = int.from_bytes(encoded[offset:offset+2], "little")
            self._send([INPUT(type=1, ki=KEYBDINPUT(wScan=unit, dwFlags=4)),
                        INPUT(type=1, ki=KEYBDINPUT(wScan=unit, dwFlags=6))])
        return self.info()

    def scroll(self, x, y, steps):
        if type(steps) is not int or not -100 <= steps <= 100:
            raise ValueError("steps must be an integer between -100 and 100")
        self._point(x, y)
        self._send([INPUT(type=0, mi=MOUSEINPUT(mouseData=(steps * 120) & 0xffffffff, dwFlags=0x800))])
        return self.info()

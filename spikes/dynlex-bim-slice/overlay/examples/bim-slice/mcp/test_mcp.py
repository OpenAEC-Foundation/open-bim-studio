# SPDX-License-Identifier: MPL-2.0
"""Headless checks; no native window or application is opened."""
import base64
import json
import http.client
import os
from pathlib import Path
import select
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import open_bim_studio_mcp as server
import windows_ui
import open_bim_studio_http as http_api

MCP_DIRECTORY = Path(__file__).resolve().parent


class ProtocolTests(unittest.TestCase):
    def call(self, name, arguments=None):
        return server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                              "params": {"name": name, "arguments": arguments or {}}})

    def test_initialize_and_ui_tool_discovery(self):
        result = server.handle({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})
        self.assertEqual(result["id"], 0)
        self.assertEqual(result["result"]["serverInfo"]["name"], "open-bim-studio")
        listed = server.handle({"id": 1, "method": "tools/list"})["result"]["tools"]
        self.assertTrue({"ui_window", "ui_click", "ui_key", "ui_type", "ui_scroll", "create_wall"}
                        <= {tool["name"] for tool in listed})

    def test_invalid_arguments_are_tool_errors(self):
        self.assertTrue(self.call("create_wall", {"x1": "invalid"})["result"]["isError"])
        with patch.object(server.MODELLER, "window", side_effect=ValueError("no bound app")):
            self.assertTrue(self.call("ui_click", {"x": -1, "y": 0})["result"]["isError"])
        malformed = server.handle({"id": 1, "method": "tools/call", "params": {"name": "state", "arguments": []}})
        self.assertTrue(malformed["result"]["isError"])
        self.assertIn("arguments", malformed["result"]["content"][0]["text"])

    def test_screenshot_is_image_content(self):
        with patch.object(server.MODELLER, "screenshot", return_value=b"png"):
            block = self.call("screenshot")["result"]["content"][0]
        self.assertEqual(block["mimeType"], "image/png")
        self.assertEqual(base64.b64decode(block["data"]), b"png")

    def test_malformed_messages_do_not_crash(self):
        self.assertEqual(server.handle([])["error"]["code"], -32600)
        self.assertIsNone(server.handle({"method": "notifications/initialized"}))

    def test_stdio_recovers_after_malformed_json(self):
        child = subprocess.run([sys.executable, "-B", str(MCP_DIRECTORY / "open_bim_studio_mcp.py")],
                               input='not JSON\n{"jsonrpc":"2.0","id":9,"method":"ping"}\n',
                               capture_output=True, text=True, timeout=3, cwd=MCP_DIRECTORY,
                               creationflags=0x08000000 if sys.platform == "win32" else 0)
        messages = [json.loads(line) for line in child.stdout.splitlines()]
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertEqual(messages[0]["error"]["code"], -32700)
        self.assertEqual(messages[1], {"jsonrpc": "2.0", "id": 9, "result": {}})

    def test_auto_connect_configuration(self):
        with patch.dict(os.environ, {"OPEN_BIM_STUDIO_API_FOLDER": "environment-api"}):
            config = server.parse_arguments([])
            self.assertEqual(config.api_folder, "environment-api")
            self.assertEqual(server.parse_arguments(["--api-folder", "explicit"]).api_folder, "explicit")

    def test_grid_and_cursor_tools_forward_to_native_editor(self):
        calls = [("create_grid", {"name": "A", "x1": 0, "y1": 0, "x2": 0, "y2": 10, "low": 0, "high": 3},
                  ("grid", "A", 0.0, 0.0, 0.0, 10.0, 0.0, 3.0)),
                 ("repeat_grid", {"source": "selected", "pattern": "5000 3x5400", "unit_code": 0},
                  ("gridrepeat", "selected", "5000 3x5400", 0)),
                 ("set_cursor", {"x": 1.2, "y": 3.4}, ("cursor", 1.2, 3.4))]
        for name, arguments, expected in calls:
            with self.subTest(name=name), patch.object(server.MODELLER, "request", return_value={"ok": True}) as request:
                self.assertNotIn("error", self.call(name, arguments))
                request.assert_called_once_with(*expected)


    def test_move_and_drag_tools_dispatch_and_reject_bad_arguments(self):
        from unittest.mock import Mock
        window = Mock()
        window.move.return_value = {"client_width": 800}
        window.drag.return_value = {"client_width": 800}
        with patch.object(server.MODELLER, "window", return_value=window):
            self.assertNotIn("isError", self.call("ui_move", {"x": 20, "y": 30})["result"])
            window.move.assert_called_once_with(20, 30)
            self.assertNotIn("isError", self.call("ui_drag", {"from_x": 1, "from_y": 2, "to_x": 30, "to_y": 40,
                                                              "button": "middle", "steps": 6, "duration_ms": 120})["result"])
            window.drag.assert_called_once_with(1, 2, 30, 40, "middle", 6, 120)
        for name, arguments in [("ui_move", {"x": 1.5, "y": 0}),
                                ("ui_drag", {"from_x": 0, "from_y": 0, "to_x": 1}),
                                ("ui_drag", {"from_x": 0, "from_y": 0, "to_x": 1, "to_y": 2, "button": "other"}),
                                ("ui_drag", {"from_x": 0, "from_y": 0, "to_x": 1, "to_y": 2, "steps": True})]:
            with self.subTest(name=name), patch.object(server.MODELLER, "window") as bound:
                self.assertTrue(self.call(name, arguments)["result"]["isError"])
                bound.assert_not_called()

    def test_type_tools_forward_stable_ids_fields_and_unicode(self):
        calls = [("list_types", {}, ("types",)),
                 ("list_types", {"tab": 7}, ("types", 7)),
                 ("create_type", {"tab": 1}, ("typeadd", 1)),
                 ("duplicate_type", {"tab": 0, "id": 123}, ("typeduplicate", 0, 123)),
                 ("set_type_field", {"tab": 0, "id": 123, "field": 0, "value": "Béton 漢字"},
                  ("typeset", 0, 123, 0, "Béton 漢字")),
                 ("set_type_field", {"tab": 1, "id": 123, "field": 2, "value": "250", "layer": 2},
                  ("typeset", 1, 123, 2, "250", 2)),
                 ("apply_type", {"tab": 5, "id": 123}, ("typeapply", 5, 123)),
                 ("delete_type", {"tab": 7, "id": 123}, ("typedelete", 7, 123)),
                 ("tool_options", {}, ("options",))]
        for name, arguments, expected in calls:
            with self.subTest(name=name, arguments=arguments), patch.object(server.MODELLER, "request", return_value={"ok": True}) as request:
                response = self.call(name, arguments)["result"]
                self.assertNotIn("isError", response)
                self.assertEqual(json.loads(response["content"][0]["text"]), {"ok": True})
                request.assert_called_once_with(*expected)

    def test_type_schema_errors_are_refused_before_native_request(self):
        for name, arguments in [("list_types", {"tab": 9}), ("create_type", {"tab": 1.5}),
                                ("duplicate_type", {"tab": 0, "id": "123"}),
                                ("set_type_field", {"tab": 0, "id": 123, "field": 7, "value": "1"}),
                                ("set_type_field", {"tab": 0, "id": 123, "field": 2, "value": 250}),
                                ("tool_options", {"extra": True})]:
            with self.subTest(name=name), patch.object(server.MODELLER, "request") as request:
                self.assertTrue(self.call(name, arguments)["result"]["isError"])
                request.assert_not_called()
        with patch.object(server.MODELLER, "request", side_effect=server.ToolError("type is in use")):
            self.assertTrue(self.call("delete_type", {"tab": 0, "id": 123})["result"]["isError"])

class TransportTests(unittest.TestCase):
    def test_multiple_clients_cannot_overwrite_single_native_slot(self):
        with tempfile.TemporaryDirectory() as directory:
            errors, received = [], []

            def app():
                try:
                    deadline = time.monotonic() + 6
                    request = Path(directory) / "request"
                    while len(received) < 2 and time.monotonic() < deadline:
                        if not request.exists():
                            time.sleep(.005)
                            continue
                        lines = request.read_text(encoding="utf-8").splitlines()
                        request.unlink()
                        # Leave the response slot occupied long enough to expose a racing client.
                        time.sleep(.1)
                        received.append(lines[-1])
                        temporary = Path(directory) / "response.tmp"
                        temporary.write_text(lines[0] + '\n' + json.dumps({"ok": True, "value": lines[-1]}), encoding="utf-8")
                        temporary.replace(Path(directory) / "response")
                except Exception as error:
                    errors.append(error)

            responder = threading.Thread(target=app)
            responder.start()
            script = ('import json,sys; from pathlib import Path; import open_bim_studio_mcp as s; '
                      'm=s.Modeller(); m.folder=Path(sys.argv[1]); '
                      'print(json.dumps(m.request("property", 10, sys.argv[2], timeout=4)))')
            children = [subprocess.Popen([sys.executable, "-B", "-c", script, directory, value],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=MCP_DIRECTORY,
                                         creationflags=0x08000000 if sys.platform == "win32" else 0)
                        for value in ("first", "second")]
            try:
                results = [child.communicate(timeout=7) for child in children]
                self.assertEqual([child.returncode for child in children], [0, 0], results)
                self.assertEqual([json.loads(out)["value"] for out, _ in results], ["first", "second"])
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                        child.wait()
                responder.join(7)
            self.assertFalse(errors)
            self.assertCountEqual(received, ["first", "second"])

    def test_atomic_utf8_request_and_matching_response(self):
        with tempfile.TemporaryDirectory() as directory:
            modeller = server.Modeller()
            modeller.folder = Path(directory)
            received = []

            def app():
                deadline = time.monotonic() + 2
                request = Path(directory) / "request"
                while not request.exists() and time.monotonic() < deadline:
                    time.sleep(.005)
                content = request.read_bytes().decode("utf-8")
                received.append(content)
                request.unlink()
                identifier = content.splitlines()[0]
                response = Path(directory) / "response.tmp"
                response.write_bytes((identifier + '\n' + json.dumps({"ok": True, "name": "Gevel café 漢字"},
                                     ensure_ascii=False)).encode("utf-8"))
                response.replace(Path(directory) / "response")

            responder = threading.Thread(target=app)
            responder.start()
            try:
                answer = modeller.request("property", 10, "Gevel café 漢字", timeout=2)
            finally:
                responder.join(3)
            self.assertEqual(answer["name"], "Gevel café 漢字")
            self.assertIn("Gevel café 漢字\n", received[0])
            self.assertFalse((Path(directory) / "request.tmp").exists())

    def test_no_connection_and_line_injection_fail(self):
        with self.assertRaises(server.ToolError):
            server.Modeller().request("state")
        with tempfile.TemporaryDirectory() as directory:
            modeller = server.Modeller()
            modeller.folder = Path(directory)
            with self.assertRaisesRegex(server.ToolError, "line"):
                modeller.request("property", 10, "name\nundo", timeout=.01)
            self.assertFalse((Path(directory) / "request").exists())

    def test_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            modeller = server.Modeller()
            modeller.folder = Path(directory)
            with self.assertRaisesRegex(server.ToolError, "no answer"):
                modeller.request("state", timeout=.01)

    def test_stale_response_does_not_match_new_request(self):
        with tempfile.TemporaryDirectory() as directory:
            modeller = server.Modeller()
            modeller.folder = Path(directory)
            (modeller.folder / "response").write_text('old\n{"ok":true}', encoding="utf-8")
            with self.assertRaises(server.ToolError):
                modeller.request("state", timeout=.01)
            self.assertFalse((modeller.folder / "response").exists())


class WindowSafetyTests(unittest.TestCase):
    def drag_window(self):
        from unittest.mock import Mock
        ui = windows_ui.WindowsUI.__new__(windows_ui.WindowsUI)
        ui.user = Mock()
        ui.user.GetAsyncKeyState.return_value = 0
        ui.user.GetForegroundWindow.return_value = 10
        ui.user.SetCursorPos.return_value = True
        ui.user.SendInput.side_effect = lambda count, *_: count
        ui.bind = Mock(return_value={"hwnd": 10})
        ui.rect = Mock(return_value=(100, 80, 900, 680))
        ui._hit = Mock()
        ui._foreground = Mock(return_value=10)
        ui.info = Mock(return_value={"client_width": 800, "client_height": 600})
        return ui

    def mouse_flags(self, ui):
        return [call.args[1][0].mi.dwFlags for call in ui.user.SendInput.call_args_list]

    def test_click_and_key_hold_down_then_release_in_separate_calls(self):
        from unittest.mock import Mock
        ui = self.drag_window()
        order = []
        ui._hold_input = Mock(side_effect=lambda *_: order.append("hold"))
        original_send = ui.user.SendInput.side_effect
        ui.user.SendInput.side_effect = lambda count, events, size: (order.append("down" if events[0].mi.dwFlags == 2 else "up"), original_send(count, events, size))[1]
        ui.click(20, 30)
        self.assertEqual(self.mouse_flags(ui), [2, 4])
        self.assertEqual(order, ["down", "hold", "up"])
        ui = self.drag_window()
        ui._hold_input = Mock()
        ui.key("ctrl+shift+s")
        calls = ui.user.SendInput.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual([(event.ki.wVk, event.ki.dwFlags) for event in calls[0].args[1]],
                         [(0x11, 0), (0x10, 0), (ord("S"), 0)])
        self.assertEqual([(event.ki.wVk, event.ki.dwFlags) for event in calls[1].args[1]],
                         [(ord("S"), 2), (0x10, 2), (0x11, 2)])
        ui._hold_input.assert_called_once()

    def test_click_and_key_release_if_hold_detects_foreground_loss(self):
        from unittest.mock import Mock
        for operation in ("click", "key"):
            ui = self.drag_window()
            def lose_focus(*_):
                ui.user.GetForegroundWindow.return_value = 99
                raise ValueError("foreground changed")
            ui._hold_input = Mock(side_effect=lose_focus)
            with self.assertRaisesRegex(ValueError, "foreground"):
                if operation == "click":
                    ui.click(20, 30)
                else:
                    ui.key("ctrl+z")
            calls = ui.user.SendInput.call_args_list
            self.assertEqual(len(calls), 2)
            if operation == "click":
                self.assertEqual(self.mouse_flags(ui), [2, 4])
            else:
                self.assertEqual([event.ki.dwFlags for event in calls[1].args[1]], [2, 2])
            ui._foreground.assert_called_once()
            ui.user.SetForegroundWindow.assert_not_called()
        ui = self.drag_window()
        ui.user.GetAsyncKeyState.side_effect = lambda key: 0x8000 if key == 0x11 else 0
        with self.assertRaisesRegex(ValueError, "modifier"):
            ui.key("enter")
        ui.user.SendInput.assert_not_called()

    def test_navigation_keys_use_explicit_extended_scancodes_on_down_and_release(self):
        from unittest.mock import Mock
        navigation = {"pageup": 0x49, "pagedown": 0x51, "end": 0x4F, "home": 0x47,
                      "left": 0x4B, "up": 0x48, "right": 0x4D, "down": 0x50,
                      "insert": 0x52, "delete": 0x53}
        for name, code in navigation.items():
            with self.subTest(name=name):
                ui = self.drag_window()
                ui._hold_input = Mock()
                ui._wait_released = Mock()
                ui.key(name)
                calls = ui.user.SendInput.call_args_list
                self.assertEqual(len(calls), 2)
                self.assertEqual((calls[0].args[1][0].ki.wVk, calls[0].args[1][0].ki.wScan,
                                  calls[0].args[1][0].ki.dwFlags), (0, code, 9))
                self.assertEqual((calls[1].args[1][0].ki.wVk, calls[1].args[1][0].ki.wScan,
                                  calls[1].args[1][0].ki.dwFlags), (0, code, 11))

    def test_ctrl_home_uses_extended_home_and_normal_ctrl_in_release_order(self):
        from unittest.mock import Mock
        ui = self.drag_window()
        ui._hold_input = Mock()
        ui._wait_released = Mock()
        ui.key("ctrl+home")
        calls = ui.user.SendInput.call_args_list
        self.assertEqual([(event.ki.wVk, event.ki.wScan, event.ki.dwFlags) for event in calls[0].args[1]],
                         [(0x11, 0, 0), (0, 0x47, 9)])
        self.assertEqual([(event.ki.wVk, event.ki.wScan, event.ki.dwFlags) for event in calls[1].args[1]],
                         [(0, 0x47, 11), (0x11, 0, 2)])

    def test_extended_key_release_survives_foreground_loss(self):
        from unittest.mock import Mock
        ui = self.drag_window()
        def lose_focus(*_):
            ui.user.GetForegroundWindow.return_value = 99
            raise ValueError("foreground changed")
        ui._hold_input = Mock(side_effect=lose_focus)
        with self.assertRaisesRegex(ValueError, "foreground"):
            ui.key("ctrl+home")
        calls = ui.user.SendInput.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual([(event.ki.wVk, event.ki.wScan, event.ki.dwFlags) for event in calls[1].args[1]],
                         [(0, 0x47, 11), (0x11, 0, 2)])
        ui._foreground.assert_called_once()
        ui.user.SetForegroundWindow.assert_not_called()

    def test_non_navigation_keys_keep_virtual_key_input(self):
        from unittest.mock import Mock
        for name, code in [("enter", 0x0D), ("tab", 9), ("escape", 0x1B), ("backspace", 8), ("f8", 0x77), ("w", ord("W"))]:
            with self.subTest(name=name):
                ui = self.drag_window()
                ui._hold_input = Mock()
                ui._wait_released = Mock()
                ui.key(name)
                calls = ui.user.SendInput.call_args_list
                self.assertEqual((calls[0].args[1][0].ki.wVk, calls[0].args[1][0].ki.wScan,
                                  calls[0].args[1][0].ki.dwFlags), (code, 0, 0))
                self.assertEqual((calls[1].args[1][0].ki.wVk, calls[1].args[1][0].ki.wScan,
                                  calls[1].args[1][0].ki.dwFlags), (code, 0, 2))

    def test_hold_is_eighty_milliseconds_with_bounded_focus_checks(self):
        ui = self.drag_window()
        elapsed = [0.0]
        sleeps = []
        def pause(seconds):
            sleeps.append(seconds)
            elapsed[0] += seconds
        with patch.object(windows_ui.time, "monotonic", side_effect=lambda: elapsed[0]), patch.object(windows_ui.time, "sleep", side_effect=pause):
            ui._hold_input()
        self.assertGreaterEqual(elapsed[0], .08)
        self.assertTrue(sleeps)
        self.assertLessEqual(max(sleeps), .02)
        self.assertGreaterEqual(ui.user.GetForegroundWindow.call_count, 4)

    def test_zero_duration_drag_still_holds_at_start_before_moving(self):
        from unittest.mock import Mock
        ui = self.drag_window()
        order = []
        ui.user.SetCursorPos.side_effect = lambda *_: (order.append("move"), True)[1]
        ui.user.SendInput.side_effect = lambda count, events, _: (order.append("down" if events[0].mi.dwFlags == 2 else "up"), count)[1]
        ui._hold_input = Mock(side_effect=lambda *_: order.append("hold"))
        ui.drag(0, 0, 40, 20, steps=1, duration_ms=0)
        self.assertEqual(order, ["move", "down", "hold", "move", "up"])
        ui._hold_input.assert_called_once()

    def test_move_uses_bound_client_point_without_mouse_buttons(self):
        ui = self.drag_window()
        self.assertEqual(ui.move(20, 30)["client_width"], 800)
        ui.user.SetCursorPos.assert_called_once_with(120, 110)
        ui.user.SendInput.assert_not_called()
        with self.assertRaisesRegex(ValueError, "outside"):
            ui.move(800, 0)

    def test_drag_checks_both_endpoints_path_and_parameters_before_button_down(self):
        for values in [(0, 0, 800, 0), (-1, 0, 10, 10), (0, 0, 10, 600)]:
            ui = self.drag_window()
            with self.assertRaisesRegex(ValueError, "outside"):
                ui.drag(*values, duration_ms=0)
            ui.user.SendInput.assert_not_called()
        for extra in [{"button": "other"}, {"steps": 0}, {"steps": 121}, {"steps": True},
                      {"duration_ms": -1}, {"duration_ms": 2001}, {"duration_ms": float("nan")}]:
            ui = self.drag_window()
            with self.assertRaises(ValueError):
                ui.drag(0, 0, 10, 10, **extra)
            ui.user.SendInput.assert_not_called()
        ui = self.drag_window()
        ui._hit.side_effect = ValueError("covered")
        with self.assertRaisesRegex(ValueError, "covered"):
            ui.drag(0, 0, 10, 10, duration_ms=0)
        ui.user.SendInput.assert_not_called()

    def test_drag_releases_button_on_success_and_motion_failure(self):
        for button, flags in [("left", [2, 4]), ("right", [8, 16]), ("middle", [32, 64])]:
            ui = self.drag_window()
            ui.drag(0, 0, 40, 20, button, steps=4, duration_ms=0)
            self.assertEqual(self.mouse_flags(ui), flags)
            self.assertEqual(ui.user.SetCursorPos.call_args.args, (140, 100))
            ui._foreground.assert_called_once()
        ui = self.drag_window()
        ui.user.SetCursorPos.side_effect = [True, False]
        with self.assertRaisesRegex(ValueError, "pointer"):
            ui.drag(0, 0, 40, 20, steps=4, duration_ms=0)
        self.assertEqual(self.mouse_flags(ui), [2, 4])

    def test_drag_refuses_foreground_change_without_refocusing_and_still_releases(self):
        ui = self.drag_window()
        def send(count, events, _):
            if events[0].mi.dwFlags == 2:
                ui.user.GetForegroundWindow.return_value = 99
            return count
        ui.user.SendInput.side_effect = send
        with self.assertRaisesRegex(ValueError, "foreground"):
            ui.drag(0, 0, 40, 20, steps=4, duration_ms=0)
        self.assertEqual(self.mouse_flags(ui), [2, 4])
        ui._foreground.assert_called_once()
        ui.user.SetForegroundWindow.assert_not_called()
        self.assertEqual(ui.user.SetCursorPos.call_count, 1)

    def test_drag_releases_after_mid_path_occlusion_and_reports_release_failure(self):
        ui = self.drag_window()
        def cover_after_down(count, events, _):
            if events[0].mi.dwFlags == 2:
                ui._hit.side_effect = ValueError("covered")
            return count
        ui.user.SendInput.side_effect = cover_after_down
        with self.assertRaisesRegex(ValueError, "covered"):
            ui.drag(0, 0, 40, 20, steps=4, duration_ms=0)
        self.assertEqual(self.mouse_flags(ui), [2, 4])
        ui = self.drag_window()
        ui.user.SendInput.side_effect = [0, 0]
        with self.assertRaisesRegex(ValueError, "could not release"):
            ui.drag(0, 0, 40, 20, duration_ms=0)
        self.assertEqual(self.mouse_flags(ui), [2, 4])

    def test_drag_releases_after_resize_or_button_down_error_and_rejects_held_buttons(self):
        ui = self.drag_window()
        def send(count, events, _):
            if events[0].mi.dwFlags == 2:
                ui.rect.return_value = (100, 80, 500, 380)
            return count
        ui.user.SendInput.side_effect = send
        with self.assertRaisesRegex(ValueError, "moved or resized"):
            ui.drag(0, 0, 40, 20, steps=4, duration_ms=0)
        self.assertEqual(self.mouse_flags(ui), [2, 4])
        ui = self.drag_window()
        ui.user.SendInput.side_effect = [0, 1]
        with self.assertRaisesRegex(ValueError, "rejected"):
            ui.drag(0, 0, 40, 20, duration_ms=0)
        self.assertEqual(self.mouse_flags(ui), [2, 4])
        for operation in ("move", "drag"):
            ui = self.drag_window()
            ui.user.GetAsyncKeyState.side_effect = lambda key: 0x8000 if key == 1 else 0
            with self.assertRaisesRegex(ValueError, "mouse buttons"):
                getattr(ui, operation)(*( (0, 0) if operation == "move" else (0, 0, 40, 20)))
            ui.user.SendInput.assert_not_called()

    def test_client_coordinates_and_bounds(self):
        rect = (-100, 80, 700, 680)
        self.assertEqual(windows_ui.client_point(rect, 20, 30), (-80, 110))
        for x, y in [(-1, 0), (800, 0), (0, 600), (float("nan"), 1), (True, 1), (1.5, 1)]:
            with self.assertRaises(ValueError):
                windows_ui.client_point(rect, x, y)

    def test_occlusion_and_windows_abi_layout(self):
        import ctypes
        self.assertTrue(windows_ui.overlaps((0, 0, 800, 600), (12, 14, 40, 60)))
        self.assertFalse(windows_ui.overlaps((0, 0, 800, 600), (800, 0, 900, 600)))
        if sys.platform == "win32":
            self.assertEqual(ctypes.sizeof(windows_ui.BITMAPINFOHEADER), 40)
            self.assertEqual(ctypes.sizeof(windows_ui.INPUT), 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)

    def test_window_binding_refuses_ambiguity_or_wrong_process(self):
        windows = [{"hwnd": 1, "pid": 10, "title": "Open BIM Studio", "executable": "C:/app/open-bim-studio.exe"},
                   {"hwnd": 2, "pid": 20, "title": "Open BIM Studio", "executable": "C:/app/open-bim-studio-dev.exe"}]
        self.assertEqual(windows_ui.choose_window(windows, 20)["hwnd"], 2)
        with self.assertRaisesRegex(ValueError, "multiple"):
            windows_ui.choose_window(windows)
        with self.assertRaisesRegex(ValueError, "no matching"):
            windows_ui.choose_window([dict(windows[0], executable="C:/other/editor.exe")])

    def test_png_encoder_dimensions_and_signature(self):
        png = windows_ui.png_from_bgra(2, 1, bytes([0, 0, 255, 0, 255, 0, 0, 0]))
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", png[16:24]), (2, 1))

    def test_key_validation(self):
        self.assertEqual(windows_ui.key_codes("ctrl+shift+s"), [0x11, 0x10, ord("S")])
        with self.assertRaises(ValueError):
            windows_ui.key_codes("win+r")
        with self.assertRaises(ValueError):
            windows_ui.key_codes("alt+tab")

    def test_binding_rejects_reused_window_or_process(self):
        from unittest.mock import Mock
        ui = windows_ui.WindowsUI.__new__(windows_ui.WindowsUI)
        ui.bound = {"hwnd": 1, "pid": 20, "executable": "app.exe", "created": 100}
        ui.user = Mock()
        ui.user.IsWindow.return_value = True
        ui._identity = Mock(return_value=dict(ui.bound, created=101))
        with self.assertRaisesRegex(ValueError, "identity changed"):
            ui.bind()
        ui.user.IsWindow.return_value = False
        with self.assertRaisesRegex(ValueError, "closed"):
            ui.bind()

    def test_input_refuses_foreign_foreground_and_obscured_point(self):
        from unittest.mock import Mock
        ui = windows_ui.WindowsUI.__new__(windows_ui.WindowsUI)
        ui.bind = Mock(return_value={"hwnd": 10})
        ui.user = Mock()
        ui.user.GetForegroundWindow.return_value = 11
        with self.assertRaisesRegex(ValueError, "foreground"):
            ui._send([])
        ui.user.SendInput.assert_not_called()
        ui.user.GetAncestor.return_value = 11
        with self.assertRaisesRegex(ValueError, "covered"):
            ui._hit(1, 2)


class HttpSmokeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.modeller = server.Modeller()
        self.modeller.folder = Path(self.directory.name)
        self.listener = http_api.create_server(self.modeller, port=0)
        self.worker = threading.Thread(target=self.listener.serve_forever, daemon=True)
        self.worker.start()

    def tearDown(self):
        self.listener.shutdown()
        self.listener.server_close()
        self.worker.join(2)
        self.directory.cleanup()

    def request(self, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.listener.server_port, timeout=3)
        try:
            connection.request("POST" if body is not None else "GET", path, body=body,
                               headers=headers or {"Content-Type": "application/json"})
            response = connection.getresponse()
            return response.status, json.loads(response.read()), dict(response.getheaders())
        finally:
            connection.close()

    def test_http_utf8_round_trip_to_native_folder(self):
        received = []
        failures = []

        def app():
            try:
                deadline = time.monotonic() + 3
                request = self.modeller.folder / "request"
                while not request.exists() and time.monotonic() < deadline:
                    time.sleep(.005)
                lines = request.read_text(encoding="utf-8").splitlines()
                request.unlink()
                received.extend(lines[1:])
                temporary = self.modeller.folder / "response.tmp"
                temporary.write_bytes((lines[0] + '\n{"ok":true,"value":"café 漢字"}').encode("utf-8"))
                temporary.replace(self.modeller.folder / "response")
            except Exception as error:
                failures.append(error)

        responder = threading.Thread(target=app)
        responder.start()
        try:
            status, result, headers = self.request("/api", json.dumps(
                {"verb": "property", "arguments": [10, "café 漢字"]}, ensure_ascii=False).encode("utf-8"))
        finally:
            responder.join(4)
        self.assertFalse(failures)
        self.assertEqual(status, 200)
        self.assertEqual(result, {"ok": True, "value": "café 漢字"})
        self.assertEqual(received, ["property", "10", "café 漢字"])
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_http_type_verbs_and_tools_share_dispatch(self):
        verbs = {"types", "typeadd", "typeduplicate", "typeset", "typeapply", "typedelete", "options"}
        self.assertTrue(verbs <= http_api.VERBS)
        with patch.object(self.modeller, "request", return_value={"ok": True, "id": 123}) as request:
            status, result, _ = self.request("/api", json.dumps(
                {"verb": "typeset", "arguments": [0, 123, 0, "Béton 漢字"]}, ensure_ascii=False).encode("utf-8"))
            self.assertEqual((status, result), (200, {"ok": True, "id": 123}))
            request.assert_called_once_with("typeset", 0, 123, 0, "Béton 漢字")
        with patch.object(self.modeller, "request", return_value={"ok": True, "types": []}) as request:
            status, result, _ = self.request("/tools/list_types", b'{"tab":7}')
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(result["content"][0]["text"]), {"ok": True, "types": []})
            request.assert_called_once_with("types", 7)

    def test_http_rejects_origin_host_non_json_and_bad_payload(self):
        self.assertEqual(self.request("/health")[0], 200)
        self.assertEqual(self.request("/api", b'{}', {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("/api", b'{}', {"Content-Type": "application/json", "Origin": "https://example.test"})[0], 403)
        self.assertEqual(self.request("/health", headers={"Host": "example.test"})[0], 403)
        for body in (b'[]', b'{', b'{"verb":"unknown"}', b'{"verb":"wall","arguments":[NaN]}'):
            self.assertEqual(self.request("/api", body)[0], 400)
        self.assertFalse((self.modeller.folder / "request").exists())

    def test_http_move_and_drag_use_bound_window_tools(self):
        from unittest.mock import Mock
        window = Mock()
        window.move.return_value = {"client_width": 800}
        window.drag.return_value = {"client_width": 800}
        with patch.object(self.modeller, "window", return_value=window):
            status, result, _ = self.request("/tools/ui_move", b'{"x":30,"y":40}')
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(result["content"][0]["text"]), {"client_width": 800})
            window.move.assert_called_once_with(30, 40)
            status, result, _ = self.request("/tools/ui_drag", b'{"from_x":30,"from_y":40,"to_x":100,"to_y":200}')
            self.assertEqual(status, 200)
            self.assertNotIn("isError", result)
            window.drag.assert_called_once_with(30, 40, 100, 200, "left", 12, 180)

    def test_http_tool_image_uses_same_dispatch(self):
        image = {"content": [{"type": "image", "mimeType": "image/png", "data": "cG5n"}]}
        with patch.object(self.modeller, "screenshot", return_value=b"png"):
            status, result, _ = self.request("/tools/screenshot", b'{}')
        self.assertEqual((status, result), (200, image))

    def test_rejected_post_consumes_its_framed_body_before_closing(self):
        # Headers and body can arrive separately: rejecting/closing on headers alone
        # races the client's write and can replace the error response with a TCP reset.
        connection = socket.create_connection(("127.0.0.1", self.listener.server_port), timeout=3)
        try:
            headers = (f"POST /api HTTP/1.1\r\nHost: 127.0.0.1:{self.listener.server_port}\r\n"
                       "Origin: https://example.test\r\nContent-Type: application/json\r\n"
                       "Content-Length: 2\r\n\r\n").encode("ascii")
            connection.sendall(headers)
            readable, _, _ = select.select([connection], [], [], .05)
            self.assertFalse(readable, "server closed/replied before consuming the framed request body")
            connection.sendall(b"{}")
            response = http.client.HTTPResponse(connection)
            response.begin()
            self.assertEqual(response.status, 403)
            self.assertIn("browser-origin", json.loads(response.read())["error"])
        finally:
            connection.close()

    def test_http_rejects_missing_or_ambiguous_framing(self):
        for lengths in ([], ["2", "2"]):
            with self.subTest(lengths=lengths):
                connection = http.client.HTTPConnection("127.0.0.1", self.listener.server_port, timeout=3)
                try:
                    connection.putrequest("POST", "/api")
                    connection.putheader("Content-Type", "application/json")
                    for value in lengths:
                        connection.putheader("Content-Length", value)
                    connection.endheaders()
                    response = connection.getresponse()
                    self.assertEqual(response.status, 400)
                    response.read()
                finally:
                    connection.close()
        self.assertEqual(self.request("/api", b'{}', {"Content-Type": "application/json", "Transfer-Encoding": "chunked"})[0], 400)


if __name__ == "__main__":
    unittest.main()

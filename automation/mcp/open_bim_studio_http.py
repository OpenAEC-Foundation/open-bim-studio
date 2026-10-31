#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Optional loopback-only JSON interface to the native editor and MCP tools."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path

import open_bim_studio_mcp as mcp


VERBS = {"ping", "state", "elements", "buttons", "button", "ribbon", "key", "pointer", "click", "press", "release",
         "select", "properties", "property", "wall", "slab", "system", "systemtypes", "undo", "redo", "fit", "tab",
         "grid", "gridrepeat", "cursor", "types", "typeadd", "typeduplicate", "typeset", "typeapply", "typedelete", "options"}
MAX_BODY = 1024 * 1024


def reject_constant(value):
    raise ValueError(f"non-finite JSON number: {value}")


def create_server(modeller=None, port=8765, dispatch=None):
    """Construct without starting a thread; all transport operations are serialized."""
    modeller = modeller or mcp.MODELLER
    dispatch = dispatch or (lambda message: mcp.handle(message, modeller))

    class Handler(BaseHTTPRequestHandler):
        # Close each request to keep framing strict and avoid request smuggling.
        protocol_version = "HTTP/1.0"

        def log_message(self, *_):
            pass

        def answer(self, status, payload):
            content = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)

        def check_client(self):
            allowed_hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if len(self.headers.get_all("Host", [])) != 1 or self.headers.get("Host", "").lower() not in allowed_hosts:
                self.answer(403, {"ok": False, "error": "Host must name this loopback endpoint"})
                return False
            # There is no browser frontend on this endpoint. Refuse all browser-origin requests,
            # including Origin:null, rather than granting CORS or trusting DNS aliases.
            if "Origin" in self.headers or self.headers.get("Sec-Fetch-Site", "none") != "none":
                self.answer(403, {"ok": False, "error": "browser-origin requests are not allowed"})
                return False
            return True

        def do_GET(self):
            if not self.check_client():
                return
            if self.path != "/health":
                self.answer(404, {"ok": False, "error": "unknown endpoint"})
                return
            self.answer(200, {"ok": True, "server": mcp.SERVER_INFO,
                              "api_folder": str(modeller.folder) if modeller.folder else None,
                              "api_configured": modeller.folder is not None,
                              "transport": "loopback-http-to-native-folder"})

        def do_POST(self):
            lengths = self.headers.get_all("Content-Length", [])
            if "Transfer-Encoding" in self.headers or len(lengths) != 1:
                self.answer(400, {"ok": False, "error": "one Content-Length is required; chunked encoding is not supported"})
                return
            try:
                length = int(lengths[0])
                if not 0 < length <= MAX_BODY:
                    raise ValueError("JSON body must be between 1 byte and 1 MiB")
                self.connection.settimeout(10)
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError("incomplete JSON body")
            except (ValueError, OSError) as error:
                self.answer(400, {"ok": False, "error": str(error)})
                return
            # Consume a well-framed body before rejecting its headers. HTTP clients
            # may write headers/body separately; closing with unread incoming bytes
            # can reset the TCP connection and discard the intended JSON error.
            if not self.check_client():
                return
            if self.headers.get_content_type() != "application/json":
                self.answer(415, {"ok": False, "error": "Content-Type must be application/json"})
                return
            try:
                payload = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
                if not isinstance(payload, dict):
                    raise ValueError("JSON body must be an object")
            except (ValueError, UnicodeError, OSError) as error:
                self.answer(400, {"ok": False, "error": str(error)})
                return
            try:
                with self.server.operation_lock:
                    if self.path == "/api":
                        if set(payload) - {"verb", "arguments"}:
                            raise ValueError("use verb and optional arguments fields")
                        verb, arguments = payload.get("verb"), payload.get("arguments", [])
                        if not isinstance(verb, str) or verb not in VERBS:
                            raise ValueError("unknown native API verb")
                        if not isinstance(arguments, list) or any(type(arg) not in (str, int, float) for arg in arguments):
                            raise ValueError("arguments must be an array of strings or numbers")
                        if any(isinstance(arg, float) and not math.isfinite(arg) for arg in arguments):
                            raise ValueError("arguments must be finite")
                        result = modeller.request(verb, *arguments)
                        self.answer(200, result)
                    elif self.path.startswith("/tools/") and self.path.count("/") == 2:
                        name = self.path[len("/tools/"):]
                        if name not in mcp.TOOLS:
                            self.answer(404, {"ok": False, "error": "unknown tool"})
                            return
                        result = dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                           "params": {"name": name, "arguments": payload}})
                        if "error" in result:
                            self.answer(400, {"ok": False, "error": result["error"]["message"]})
                        else:
                            self.answer(422 if result["result"].get("isError") else 200, result["result"])
                    else:
                        self.answer(404, {"ok": False, "error": "unknown endpoint"})
            except (ValueError, TypeError) as error:
                self.answer(400, {"ok": False, "error": str(error)})
            except (mcp.ToolError, OSError) as error:
                self.answer(503, {"ok": False, "error": str(error)})

        def do_OPTIONS(self):
            self.answer(403, {"ok": False, "error": "CORS is not enabled"})

    listener = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    listener.daemon_threads = True
    listener.operation_lock = modeller.request_lock
    return listener


def main(argv=None):
    parser = argparse.ArgumentParser(description="Open BIM Studio loopback HTTP JSON API (no CORS)")
    parser.add_argument("--api-folder", default=os.environ.get("OPEN_BIM_STUDIO_API_FOLDER"), required=False)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--port", type=int, default=8765)
    config = parser.parse_args(argv)
    if config.api_folder:
        mcp.MODELLER.folder = Path(config.api_folder).expanduser().resolve()
    mcp.MODELLER.pid = config.pid
    listener = create_server(port=config.port)
    print(f"Open BIM Studio HTTP API: http://127.0.0.1:{listener.server_port}", flush=True)
    try:
        listener.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        listener.server_close()
        mcp.MODELLER.close()


if __name__ == "__main__":
    main()

"""A minimal stdio client for automation/mcp/open_bim_studio_mcp.py.

    python3 mcp_client.py TOOL '{"arg": 1}' [TOOL '{...}' ...]

Starts the MCP server, initializes, connects it to the API folder in $OBS_API
on display $OBS_DISPLAY, then calls each tool in turn and prints its text.
"""
import json
import os
import subprocess
import sys

SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mcp", "open_bim_studio_mcp.py")


class Client:
    def __init__(self):
        self.process = subprocess.Popen([sys.executable, SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        text=True, encoding="utf-8")
        self.counter = 0
        self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                "clientInfo": {"name": "fzk-rebuild", "version": "1"}})
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.process.stdin.flush()

    def rpc(self, method, params):
        self.counter += 1
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.counter, "method": method,
                                             "params": params}) + "\n")
        self.process.stdin.flush()
        answer = json.loads(self.process.stdout.readline())
        if "error" in answer:
            raise RuntimeError(answer["error"])
        return answer["result"]

    def call(self, name, arguments=None):
        result = self.rpc("tools/call", {"name": name, "arguments": arguments or {}})
        texts = [c.get("text", "<%s>" % c.get("type")) for c in result.get("content", [])]
        if result.get("isError"):
            raise RuntimeError("%s: %s" % (name, " ".join(texts)))
        return "\n".join(texts), result

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=10)


def connected():
    client = Client()
    client.call("connect", {"folder": os.environ["OBS_API"], "display": os.environ.get("OBS_DISPLAY", ":0")})
    return client


if __name__ == "__main__":
    client = connected()
    words = sys.argv[1:]
    for index in range(0, len(words), 2):
        arguments = json.loads(words[index + 1]) if index + 1 < len(words) else {}
        try:
            text, _ = client.call(words[index], arguments)
            print("== %s %s\n%s" % (words[index], arguments, text))
        except RuntimeError as failure:
            print("!! %s" % failure)
    client.close()

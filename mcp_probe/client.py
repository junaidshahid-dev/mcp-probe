"""Transport to an MCP server.

Real MCP servers speak JSON-RPC 2.0 over stdio or HTTP. `StdioMCPClient` launches a server
process and speaks the protocol (initialize -> tools/list -> tools/call). To keep mcp-probe
usable and testable WITHOUT a live server or the mcp SDK installed, everything upstream depends
only on the small `MCPClient` protocol below — `FakeMCPClient` (in tests) implements the same
interface, so the checks are exercised end to end offline.
"""
from __future__ import annotations

import json
import subprocess
from typing import Protocol

from .model import ToolSpec


class ToolError(Exception):
    """Raised when the server reports a tool call was invalid/failed (a GOOD outcome for bad input)."""


class MCPClient(Protocol):
    def list_tools(self) -> list[ToolSpec]: ...
    def call_tool(self, name: str, args: dict) -> dict: ...     # returns result, or raises ToolError


class StdioMCPClient:
    """Minimal JSON-RPC-over-stdio MCP client. Launches `command` as a subprocess."""

    def __init__(self, command: list[str], timeout: float = 20.0):
        self.command = command
        self.timeout = timeout
        self.proc: subprocess.Popen | None = None
        self._id = 0

    def __enter__(self) -> "StdioMCPClient":
        self.proc = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                 "clientInfo": {"name": "mcp-probe", "version": "1.0"}})
        self._notify("notifications/initialized", {})
        return self

    def __exit__(self, *exc) -> None:
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def _send(self, obj: dict) -> None:
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _notify(self, method: str, params: dict) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _rpc(self, method: str, params: dict) -> dict:
        assert self.proc and self.proc.stdout
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        while True:                                   # skip notifications, read our response
            line = self.proc.stdout.readline()
            if not line:
                raise ToolError("server closed the connection")
            msg = json.loads(line)
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise ToolError(json.dumps(msg["error"]))
                return msg.get("result", {})

    def list_tools(self) -> list[ToolSpec]:
        res = self._rpc("tools/list", {})
        return [ToolSpec(t["name"], t.get("description", ""),
                         t.get("inputSchema", t.get("input_schema", {})),
                         t.get("execution", {}) or {})
                for t in res.get("tools", [])]

    def call_tool(self, name: str, args: dict) -> dict:
        res = self._rpc("tools/call", {"name": name, "arguments": args})
        if res.get("isError"):
            raise ToolError(json.dumps(res))
        return res

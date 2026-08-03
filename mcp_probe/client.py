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
import tempfile
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
        # MCP is JSON-RPC over UTF-8. text=True alone decodes with the LOCALE codepage, so on a
        # Windows cp1252 console any server with non-ASCII tool text (CJK descriptions, curly
        # quotes, emoji) killed the probe with UnicodeDecodeError before a single tool was
        # audited. errors="replace" keeps a malformed byte from aborting the run - it surfaces
        # as a JSON parse error attributed to the server, which is where it belongs.
        # stderr goes to a temp file rather than DEVNULL. A server that dies during startup
        # (bad args, missing dependency, incompatible SDK) otherwise produced only
        # "server closed the connection" - true, useless, and the single most common thing a
        # user hits. The traceback is on stderr; keep it and put it in the error message.
        self._stderr = tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace")
        self.proc = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self._stderr, text=True, bufsize=1,
            encoding="utf-8", errors="replace")
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
        if getattr(self, "_stderr", None):
            self._stderr.close()

    def _stderr_tail(self, limit: int = 800) -> str:
        """Last of the server's stderr, for when it dies without explaining itself."""
        try:
            self._stderr.flush()
            self._stderr.seek(0)
            text = self._stderr.read().strip()
        except Exception:                                  # closed / unreadable - not worth failing over
            return ""
        return f"\n--- server stderr (last {limit} chars) ---\n{text[-limit:]}" if text else ""

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
                raise ToolError("server closed the connection" + self._stderr_tail())
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                # Not our bug: the server wrote non-JSON to stdout (a log line, a banner, or
                # malformed UTF-8). Say so, and show what it actually sent.
                raise ToolError(
                    f"server sent non-JSON on stdout ({e}): {line[:200]!r}"
                    + self._stderr_tail()) from None
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

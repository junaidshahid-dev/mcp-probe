"""Tests drive the full probe against in-memory MCP servers of varying quality.

A FakeMCPClient implements the same interface as the real stdio client, so every check runs
offline. We include a WELL-BEHAVED server (validates inputs) and a BROKEN one (accepts garbage,
crashes on huge input) and assert mcp-probe scores them accordingly — i.e. that the auditor
actually catches the bugs it claims to catch.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from mcp_probe.client import ToolError
from mcp_probe.model import Severity, ToolSpec
from mcp_probe.probe import probe_server
from mcp_probe.report import to_markdown, to_text

ECHO_SCHEMA = {"type": "object",
               "properties": {"text": {"type": "string"}, "times": {"type": "integer"}},
               "required": ["text"]}


class WellBehavedServer:
    """Validates inputs the way a good MCP server should."""
    def list_tools(self):
        return [ToolSpec("echo", "Echo text back N times", ECHO_SCHEMA)]

    def call_tool(self, name, args):
        if name != "echo":
            raise ToolError("unknown tool")
        if "text" not in args:
            raise ToolError("missing required 'text'")
        if not isinstance(args["text"], str):
            raise ToolError("'text' must be a string")
        if "times" in args and not isinstance(args["times"], int):
            raise ToolError("'times' must be an integer")
        return {"content": args["text"] * int(args.get("times", 1))}


class BrokenServer:
    """Accepts anything (no validation) and crashes on very large input."""
    def list_tools(self):
        return [ToolSpec("echo", "", ECHO_SCHEMA)]        # note: empty description too

    def call_tool(self, name, args):
        if len(str(args.get("text", ""))) > 10_000:
            raise RuntimeError("buffer overflow simulation")   # non-ToolError => 'crash'
        return {"content": "ok"}


def test_wellbehaved_scores_high():
    r = probe_server(WellBehavedServer(), "well-behaved")
    assert r.score() >= 90 and r.grade() == "A"
    # it should have cleanly rejected the invalid cases
    checks = {(f.check, f.severity) for f in r.findings}
    assert ("missing-required", Severity.OK) in checks
    assert ("wrong-type", Severity.OK) in checks
    assert not any(f.severity is Severity.FAIL for f in r.findings)


def test_broken_server_is_flagged():
    r = probe_server(BrokenServer(), "broken")
    sev = {f.check: f.severity for f in r.findings}
    # accepts invalid input without validating -> WARN
    assert any(f.check == "wrong-type" and f.severity is Severity.WARN for f in r.findings)
    # crashes on huge string -> FAIL
    assert any(f.check == "crash" and f.severity is Severity.FAIL for f in r.findings)
    # missing description -> WARN
    assert any(f.check == "no-description" for f in r.findings)
    assert r.score() < 75          # meaningfully worse than the good server


def test_crash_stops_further_calls():
    """After a crash the probe must not keep hammering the dead server."""
    r = probe_server(BrokenServer(), "broken")
    crashes = [f for f in r.findings if f.check == "crash"]
    assert len(crashes) == 1       # exactly one crash recorded, then it stopped


def test_reports_render():
    r = probe_server(WellBehavedServer(), "well-behaved")
    txt, md = to_text(r), to_markdown(r)
    assert "score" in txt.lower() and "MCP audit" in md
    assert "echo" in md


def test_empty_server_warns():
    class Empty:
        def list_tools(self): return []
        def call_tool(self, n, a): raise ToolError("n/a")
    r = probe_server(Empty(), "empty")
    assert any(f.check == "no-tools" for f in r.findings)

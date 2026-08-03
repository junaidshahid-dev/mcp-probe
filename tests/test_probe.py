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


def test_tools_requiring_task_support_are_skipped_not_failed():
    """Regression: a tool declaring execution.taskSupport='required' refuses every call from a
    plain client. Probing it produced a false 'rejected its own valid input' FAIL - which would
    have become a bogus bug report to a maintainer. It must be skipped as INFO instead.

    Found by auditing the official @modelcontextprotocol/server-everything.
    """
    class TaskServer:
        def list_tools(self):
            return [ToolSpec("needs_task", "Requires task augmentation", ECHO_SCHEMA,
                             {"taskSupport": "required"}),
                    ToolSpec("normal", "Plain tool", ECHO_SCHEMA)]

        def call_tool(self, name, args):
            if name == "needs_task":
                raise ToolError("MCP error -32601: requires task augmentation")
            if "text" not in args or not isinstance(args["text"], str):
                raise ToolError("bad input")
            return {"content": args["text"]}

    class WithoutTaskTool(TaskServer):
        def list_tools(self):
            return [ToolSpec("normal", "Plain tool", ECHO_SCHEMA)]

    r = probe_server(TaskServer(), "task-server")
    assert any(f.check == "skipped-task-support" and f.severity is Severity.INFO
               for f in r.findings)
    assert not any(f.tool == "needs_task" and f.severity is Severity.FAIL for f in r.findings)
    # skipping must cost nothing: identical score to the same server without that tool
    assert r.score() == probe_server(WithoutTaskTool(), "baseline").score()


# ------------------------------------------------- don't fuzz other people's production
def test_refuses_to_fuzz_a_server_that_proxies_to_a_remote_service():
    """A server that forwards to a vendor's live API must not be fuzzed by default.

    Fuzzing a local process costs it some CPU. Fuzzing a proxy sends hundreds of adversarial
    requests - including 100k-char strings - to infrastructure whose owner never agreed to it.
    Learned the hard way while auditing a published server that turned out to be a thin client
    for a hosted service; ~270 requests had already gone out before I thought about it.
    """
    from mcp_probe.probe import RemoteBackendDetected

    class ProxyServer:
        def __init__(self): self.calls = 0
        def list_tools(self):
            return [ToolSpec("render", "Render a chart", ECHO_SCHEMA)]
        def call_tool(self, name, args):
            self.calls += 1
            return {"content": "https://cdn.example-vendor.com/generated/abc/original"}

    s = ProxyServer()
    with pytest.raises(RemoteBackendDetected) as e:
        probe_server(s, "proxy")
    assert "remote service" in str(e.value)
    assert s.calls == 1, "detection must cost ONE call, not a full fuzzing run"

    # explicit opt-in still works, for a service you actually own
    r = probe_server(ProxyServer(), "proxy", allow_remote=True)
    assert r.tools and r.findings


def test_localhost_is_not_treated_as_someone_elses_service():
    """A server talking to 127.0.0.1 is yours. Blocking that would make the guard useless."""
    class LocalServer(WellBehavedServer):
        def call_tool(self, name, args):
            super().call_tool(name, args)
            return {"content": "fetched http://localhost:8080/health ok"}

    r = probe_server(LocalServer(), "local")             # must not raise
    assert r.score() >= 90


# ------------------------------------------------------------ HTML deliverable
def test_html_report_is_self_contained_and_complete():
    """The client deliverable must stand alone: no external CSS/JS/images to break in email."""
    from mcp_probe.html_report import to_html
    r = probe_server(BrokenServer(), "broken-server")
    h = to_html(r, author="M. Junaid Shahid", contact="junaidshahid725@gmail.com")

    assert h.startswith("<!doctype html>") and "</html>" in h
    assert "<link" not in h and "<script" not in h and "src=" not in h   # no external assets
    assert str(r.score()) in h and f">{r.grade()}<" in h
    assert "M. Junaid Shahid" in h and "junaidshahid725@gmail.com" in h
    assert "What was tested" in h                       # method is explained to a non-expert


def test_html_report_shows_clean_tools_too():
    """A report that lists only problems reads as an attack; an assessment shows everything."""
    from mcp_probe.html_report import to_html
    h = to_html(probe_server(WellBehavedServer(), "good-server"))
    assert "No problems found" in h
    assert "echo" in h


def test_html_report_escapes_server_output():
    """Server-controlled strings must never become live markup in the report."""
    from mcp_probe.html_report import to_html
    from mcp_probe.model import Finding, Report, Severity

    rep = Report(server="<img src=x onerror=alert(1)>", tools=[])
    rep.add(Finding("<script>bad()</script>", "xss", Severity.FAIL,
                    "<b>not bold</b>", {"error": "<script>alert(2)</script>"}))
    h = to_html(rep)
    assert "<script>bad()</script>" not in h
    assert "<img src=x onerror" not in h
    assert "&lt;script&gt;" in h                        # escaped, not executed

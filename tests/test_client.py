"""Transport-level regressions for StdioMCPClient.

These launch REAL subprocesses (tiny Python scripts standing in for MCP servers), because both
bugs covered here live in process/pipe handling and are invisible to an in-memory fake.

Both were found by auditing real published MCP servers, not by writing tests first.
"""
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from mcp_probe.client import StdioMCPClient, ToolError


def _server(tmp_path: Path, body: str) -> str:
    """Write a stand-in server script and return the command that runs it."""
    f = tmp_path / "srv.py"
    f.write_text(textwrap.dedent(body), encoding="utf-8")
    return f'"{sys.executable}" "{f}"'


# A minimal server that answers initialize + tools/list. The tool description is deliberately
# non-ASCII: CJK text, a curly quote and an emoji.
UNICODE_SERVER = '''
    import json, sys
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if "id" not in msg:                       # a notification, no reply
            continue
        if msg["method"] == "initialize":
            res = {"protocolVersion": "2024-11-05", "capabilities": {}}
        elif msg["method"] == "tools/list":
            res = {"tools": [{"name": "chart",
                              "description": "\\u751f\\u6210\\u56fe\\u8868 \\u2014 don\\u2019t crash \\U0001F4CA",
                              "inputSchema": {"type": "object",
                                              "properties": {"t": {"type": "string"}},
                                              "required": ["t"]}}]}
        else:
            res = {"content": "ok"}
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res}) + "\\n")
        sys.stdout.flush()
'''


def test_non_ascii_tool_text_does_not_kill_the_probe(tmp_path):
    """Regression: stdout was decoded with the LOCALE codepage, not UTF-8.

    On a Windows cp1252 machine any server with CJK/emoji/curly-quote tool text raised
    UnicodeDecodeError inside tools/list - the audit died before testing a single tool.
    Found against a published server whose tool descriptions are partly Chinese.
    """
    import shlex
    with StdioMCPClient(shlex.split(_server(tmp_path, UNICODE_SERVER))) as c:
        tools = c.list_tools()

    assert len(tools) == 1
    assert tools[0].name == "chart"
    assert "生成图表" in tools[0].description      # CJK survived the round trip
    assert "\U0001F4CA" in tools[0].description                    # so did the emoji


DYING_SERVER = '''
    import sys
    print("ImportError: cannot import name 'McpError'", file=sys.stderr)
    sys.exit(1)
'''


def test_startup_failure_reports_the_servers_stderr(tmp_path):
    """Regression: stderr went to DEVNULL, so a server that died at startup produced only
    'server closed the connection' - true, and useless. The traceback is the whole answer.

    Found against mcp-server-time / mcp-server-git / markitdown-mcp, which all fail to start
    against mcp SDK 2.0 because they declare an unbounded `mcp>=` dependency.
    """
    import shlex
    with pytest.raises(ToolError) as e:
        with StdioMCPClient(shlex.split(_server(tmp_path, DYING_SERVER))):
            pass

    assert "server closed the connection" in str(e.value)
    assert "McpError" in str(e.value)              # the actual cause is in the message
    assert "server stderr" in str(e.value)


CHATTY_SERVER = '''
    import sys
    sys.stdout.write("Listening on stdio...\\n")     # a log line, not JSON
    sys.stdout.flush()
    sys.exit(0)
'''


def test_non_json_on_stdout_is_reported_as_the_servers_fault(tmp_path):
    """A server that prints a banner to stdout corrupts the JSON-RPC stream. Say that plainly
    instead of surfacing a bare JSONDecodeError that looks like a bug in the auditor.
    """
    import shlex
    with pytest.raises(ToolError) as e:
        with StdioMCPClient(shlex.split(_server(tmp_path, CHATTY_SERVER))):
            pass

    assert "non-JSON on stdout" in str(e.value)
    assert "Listening on stdio" in str(e.value)

"""mcp-probe CLI — audit an MCP server.

    # audit a real MCP server launched over stdio
    python -m mcp_probe.cli --cmd "python my_server.py"

    # write a Markdown audit report
    python -m mcp_probe.cli --cmd "python my_server.py" --markdown audit.md
"""
from __future__ import annotations

import argparse
import shlex
import sys

from .client import StdioMCPClient
from .probe import probe_server
from .html_report import to_html
from .report import to_markdown, to_text


def main() -> None:
    ap = argparse.ArgumentParser(prog="mcp-probe",
                                 description="Audit an MCP server: discover tools, fuzz inputs, score.")
    ap.add_argument("--cmd", required=True,
                    help='command that launches the MCP server over stdio, e.g. "python server.py"')
    ap.add_argument("--markdown", metavar="FILE", help="also write a Markdown report to FILE")
    ap.add_argument("--html", metavar="FILE",
                    help="write a self-contained HTML audit report to FILE (client deliverable)")
    ap.add_argument("--author", default="M. Junaid Shahid", help="name on the HTML report")
    ap.add_argument("--contact", default="junaidshahid725@gmail.com",
                    help="contact line on the HTML report")
    ap.add_argument("--fail-under", type=int, default=0,
                    help="exit non-zero if the score is below this (for CI). default 0 = never fail")
    a = ap.parse_args()

    with StdioMCPClient(shlex.split(a.cmd)) as client:
        report = probe_server(client, a.cmd)

    print(to_text(report))
    if a.markdown:
        with open(a.markdown, "w", encoding="utf-8") as f:
            f.write(to_markdown(report))
        print(f"\nMarkdown report -> {a.markdown}")
    if a.html:
        with open(a.html, "w", encoding="utf-8") as f:
            f.write(to_html(report, author=a.author, contact=a.contact))
        print(f"HTML report -> {a.html}")

    if report.score() < a.fail_under:
        print(f"\nscore {report.score()} < fail-under {a.fail_under}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

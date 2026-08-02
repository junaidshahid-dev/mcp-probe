"""Self-contained HTML audit report - the artifact a client actually pays for.

Terminal output is not a deliverable. This produces a single file with no external assets that
can be emailed, attached to a proposal, or forwarded to a CTO, and that reads as a professional
audit rather than a tool dump.

Design choices that matter for how it lands:
  - The score and grade are the first thing on the page, colour-coded by severity.
  - Findings are grouped by TOOL, because that's the unit an engineer fixes.
  - Every finding says what was sent and what came back, so nothing has to be taken on faith.
  - INFO findings are shown but visually quiet - they are observations, not defects, and
    inflating them is how audit reports lose credibility.
  - Clean tools are listed too. A report that only shows problems reads as an attack; one that
    shows the whole picture reads as an assessment.
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from .model import Report, Severity

_SEV = {
    Severity.FAIL: ("fail", "Failure", "Crashed or lost the connection on this input"),
    Severity.WARN: ("warn", "Warning", "Accepted invalid input, or crashed internally instead of validating"),
    Severity.INFO: ("info", "Note", "Observation, not a defect"),
    Severity.OK: ("ok", "Passed", ""),
}


def _grade_class(score: int) -> str:
    return "g-a" if score >= 90 else "g-b" if score >= 75 else "g-c" if score >= 60 else "g-f"


def to_html(report: Report, author: str = "M. Junaid Shahid",
            contact: str = "junaidshahid725@gmail.com") -> str:
    score, grade = report.score(), report.grade()
    c = report.counts()
    generated = datetime.now(timezone.utc).strftime("%d %B %Y")

    by_tool: dict[str, list] = {t.name: [] for t in report.tools}
    for f in report.findings:
        by_tool.setdefault(f.tool, []).append(f)

    # tools with real problems first - a reader should not have to hunt
    def rank(item):
        name, findings = item
        return (-sum(1 for f in findings if f.severity is Severity.FAIL),
                -sum(1 for f in findings if f.severity is Severity.WARN), name)

    blocks = []
    for name, findings in sorted(by_tool.items(), key=rank):
        problems = [f for f in findings if f.severity in (Severity.FAIL, Severity.WARN)]
        notes = [f for f in findings if f.severity is Severity.INFO]
        passed = sum(1 for f in findings if f.severity is Severity.OK)
        rows = []
        for f in problems + notes:
            cls, label, _ = _SEV[f.severity]
            detail = ""
            if f.detail:
                bits = []
                if f.detail.get("note"):
                    bits.append(f"<b>Input:</b> {html.escape(str(f.detail['note']))}")
                if f.detail.get("error"):
                    bits.append(f"<b>Server said:</b> <code>{html.escape(str(f.detail['error'])[:300])}</code>")
                if bits:
                    detail = "<div class='detail'>" + "<br>".join(bits) + "</div>"
            rows.append(
                f"<div class='finding {cls}'><div class='fhead'>"
                f"<span class='badge {cls}'>{label}</span>"
                f"<span class='check'>{html.escape(f.check)}</span></div>"
                f"<div class='msg'>{html.escape(f.message)}</div>{detail}</div>")
        status = ("clean" if not problems else
                  "fail" if any(f.severity is Severity.FAIL for f in problems) else "warn")
        summary = ("No problems found" if not problems else
                   f"{len(problems)} issue" + ("s" if len(problems) != 1 else ""))
        blocks.append(
            f"<section class='tool {status}'>"
            f"<div class='thead'><h3>{html.escape(name)}</h3>"
            f"<span class='tsum {status}'>{summary}</span></div>"
            f"<div class='tmeta'>{passed} checks passed</div>"
            f"{''.join(rows)}</section>")

    tools_list = "".join(
        f"<li><code>{html.escape(t.name)}</code> - {html.escape(t.description or 'no description')}"
        f" <span class='dim'>({len(t.properties)} params, {len(t.required)} required)</span></li>"
        for t in report.tools)

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MCP audit - {html.escape(report.server)}</title>
<style>
  :root {{ --ink:#14181f; --muted:#5c6875; --line:#e4e9ef; --bg:#f7f9fc; --panel:#fff;
    --fail:#c23b3b; --fail-bg:#fdecec; --warn:#9a6a00; --warn-bg:#fdf6e3;
    --info:#1f6feb; --info-bg:#eaf2ff; --ok:#0f7b3f; --ok-bg:#e9f7ef; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); line-height:1.55;
    font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:40px 24px 80px; }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:14px;
    padding:26px; margin-bottom:20px; }}
  h1 {{ font-size:26px; letter-spacing:-.02em; margin:0 0 4px; }}
  .sub {{ color:var(--muted); font-size:14.5px; margin:0; }}
  .server {{ font-family:ui-monospace,Consolas,monospace; font-size:13.5px; color:var(--muted);
    word-break:break-all; margin-top:8px; }}
  .scorewrap {{ display:flex; align-items:center; gap:26px; flex-wrap:wrap; }}
  .score {{ font-size:60px; font-weight:800; letter-spacing:-.03em; line-height:1; }}
  .score span {{ font-size:22px; font-weight:600; color:var(--muted); }}
  .grade {{ font-size:34px; font-weight:800; padding:10px 22px; border-radius:12px; }}
  .g-a {{ color:var(--ok); background:var(--ok-bg); }}
  .g-b {{ color:#1f6feb; background:var(--info-bg); }}
  .g-c {{ color:var(--warn); background:var(--warn-bg); }}
  .g-f {{ color:var(--fail); background:var(--fail-bg); }}
  .tallies {{ display:flex; gap:10px; flex-wrap:wrap; margin-left:auto; }}
  .tally {{ text-align:center; border:1px solid var(--line); border-radius:10px; padding:9px 16px;
    min-width:74px; }}
  .tally b {{ display:block; font-size:21px; }}
  .tally small {{ color:var(--muted); font-size:11.5px; text-transform:uppercase;
    letter-spacing:.06em; }}
  h2 {{ font-size:17px; text-transform:uppercase; letter-spacing:.07em; color:var(--muted);
    margin:34px 0 14px; }}
  .tool {{ background:var(--panel); border:1px solid var(--line); border-left-width:4px;
    border-radius:12px; padding:18px 20px; margin-bottom:12px; }}
  .tool.clean {{ border-left-color:#cfe8d8; }}
  .tool.warn {{ border-left-color:#e6c766; }}
  .tool.fail {{ border-left-color:var(--fail); }}
  .thead {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px; }}
  .thead h3 {{ margin:0; font-size:16px; font-family:ui-monospace,Consolas,monospace; }}
  .tsum {{ font-size:13px; font-weight:700; }}
  .tsum.clean {{ color:var(--ok); }} .tsum.warn {{ color:var(--warn); }}
  .tsum.fail {{ color:var(--fail); }}
  .tmeta {{ color:var(--muted); font-size:12.5px; margin-top:2px; }}
  .finding {{ margin-top:12px; padding:12px 14px; border-radius:9px; }}
  .finding.fail {{ background:var(--fail-bg); }} .finding.warn {{ background:var(--warn-bg); }}
  .finding.info {{ background:#f4f6f9; }}
  .fhead {{ display:flex; gap:9px; align-items:center; }}
  .badge {{ font-size:11px; font-weight:800; padding:2px 9px; border-radius:999px;
    text-transform:uppercase; letter-spacing:.05em; }}
  .badge.fail {{ background:var(--fail); color:#fff; }}
  .badge.warn {{ background:#b5820c; color:#fff; }}
  .badge.info {{ background:#c3ccd8; color:#33404f; }}
  .check {{ font-family:ui-monospace,Consolas,monospace; font-size:12.5px; color:var(--muted); }}
  .msg {{ margin-top:6px; font-size:14.5px; }}
  .detail {{ margin-top:8px; font-size:13px; color:var(--muted); }}
  .detail code {{ background:#fff; border:1px solid var(--line); border-radius:5px;
    padding:1px 5px; font-size:12.5px; word-break:break-word; }}
  ul.tools {{ list-style:none; padding:0; margin:0; font-size:14px; }}
  ul.tools li {{ padding:7px 0; border-top:1px solid var(--line); }}
  ul.tools li:first-child {{ border-top:0; }}
  .dim {{ color:var(--muted); font-size:12.5px; }}
  .method {{ font-size:14px; color:var(--muted); }}
  footer {{ margin-top:34px; padding-top:18px; border-top:1px solid var(--line);
    color:var(--muted); font-size:13px; display:flex; justify-content:space-between;
    flex-wrap:wrap; gap:10px; }}
  @media print {{ body {{ background:#fff; }} .card,.tool {{ break-inside:avoid; }} }}
</style></head><body><div class="wrap">

<div class="card">
  <h1>MCP Server Audit</h1>
  <p class="sub">Robustness and input-validation assessment &middot; {generated}</p>
  <div class="server">{html.escape(report.server)}</div>
</div>

<div class="card scorewrap">
  <div class="score">{score}<span>/100</span></div>
  <div class="grade {_grade_class(score)}">{grade}</div>
  <div class="tallies">
    <div class="tally"><b>{len(report.tools)}</b><small>Tools</small></div>
    <div class="tally"><b style="color:var(--fail)">{c['fail']}</b><small>Failures</small></div>
    <div class="tally"><b style="color:var(--warn)">{c['warn']}</b><small>Warnings</small></div>
    <div class="tally"><b style="color:var(--ok)">{c['ok']}</b><small>Passed</small></div>
  </div>
</div>

<h2>Findings by tool</h2>
{''.join(blocks)}

<h2>What was tested</h2>
<div class="card method">
  <p>Each tool's declared JSON schema was used to generate adversarial calls, one failure mode
  at a time: missing required fields, wrong types, unknown extra fields, empty strings,
  100,000-character strings, and injection-shaped payloads.</p>
  <ul>
    <li><b>Failure</b> - the server crashed or the connection was lost.</li>
    <li><b>Warning</b> - the server accepted clearly-invalid input, or crashed internally
        instead of validating it.</li>
    <li><b>Note</b> - an observation, not a defect (for example a tool that needs semantically
        real values, or one this client could not exercise).</li>
  </ul>
  <p>Each tool is scored independently and the results averaged, so a large server is not
  penalised simply for having more surface. A clean rejection of bad input counts as correct
  behaviour - that is what a well-built server should do.</p>
</div>

<h2>Tools discovered</h2>
<div class="card"><ul class="tools">{tools_list}</ul></div>

<footer>
  <div>Prepared by {html.escape(author)} &middot; {html.escape(contact)}</div>
  <div>Generated with <b>mcp-probe</b></div>
</footer>
</div></body></html>"""

"""The probe engine: run all checks against a server and build a scored Report.

Checks performed per tool:
  1. schema-hygiene  - does the tool advertise a usable input schema, description, typed props?
  2. valid-baseline  - the server should ACCEPT a schema-valid argument set
  3. rejects-invalid - the server should REJECT missing-required / wrong-type inputs
                       (cleanly, via an error - NOT by crashing the connection)
  4. robustness      - empty/huge/injection-shaped strings must not crash the server

A crash (the client can no longer talk to the server) is the worst outcome: FAIL.
A clean rejection of bad input is the BEST outcome. Silent acceptance of clearly-invalid
input is a WARN (the tool isn't validating).
"""
from __future__ import annotations

import re

from .client import MCPClient, ToolError
from .fuzz import adversarial_cases, valid_case
from .model import Finding, Report, Severity, ToolSpec

# Signatures of an UNHANDLED runtime error leaking through the error channel. A server that
# answers "input.x.toLowerCase is not a function" did not validate the input - it crashed
# internally and the exception happened to be caught. That is materially different from a
# deliberate "invalid argument" rejection, and it usually leaks implementation detail too.
_UNHANDLED = re.compile(
    r"is not a function|is not defined|cannot read propert|undefined is not|"
    r"TypeError|ReferenceError|AttributeError|NoneType|KeyError|IndexError|"
    r"Traceback|unhandled|NullPointer|panic:",
    re.I)


# Evidence that a "server" is really a thin proxy to somebody else's production backend:
# an absolute URL to an external host in the reply, or a server-side path from a container /
# serverless runtime that does not exist on this machine.
_REMOTE_BACKEND = re.compile(
    r"https?://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])[a-z0-9.-]+\.[a-z]{2,}"
    r"|/var/task/|/var/runtime/|/usr/src/app/|/opt/nodejs/",
    re.I)


class RemoteBackendDetected(Exception):
    """Raised when probing would send adversarial traffic to a third party's live service."""


def _looks_remote(client: MCPClient, spec: ToolSpec) -> str | None:
    """ONE probe call, purely to find out where the tool's work actually happens.

    Fuzzing a local process costs that process some CPU. Fuzzing a server that forwards to a
    vendor's production API sends a few hundred adversarial requests - including 100k-char
    strings - to infrastructure whose owner never agreed to it. Those are not the same act, and
    the tool should not quietly do the second one. Learning this costs a single call instead of
    the ~10-per-tool a full run would send.
    """
    try:
        result = client.call_tool(spec.name, valid_case(spec).args)
        text = str(result)
    except ToolError as e:
        text = str(e)
    except Exception:
        return None                                     # transport trouble; the run will catch it
    m = _REMOTE_BACKEND.search(text)
    return m.group(0) if m else None


def _schema_hygiene(report: Report, spec: ToolSpec) -> None:
    if not spec.description.strip():
        report.add(Finding(spec.name, "no-description", Severity.WARN,
                           "tool has no description - agents rely on it to choose the tool"))
    if not spec.input_schema:
        report.add(Finding(spec.name, "no-input-schema", Severity.WARN,
                           "tool advertises no input schema - inputs cannot be validated"))
        return
    untyped = [n for n, p in spec.properties.items() if "type" not in p]
    if untyped:
        report.add(Finding(spec.name, "untyped-params", Severity.INFO,
                           f"parameters without a declared type: {untyped}"))
    if spec.properties or spec.input_schema.get("type") == "object":
        report.add(Finding(spec.name, "schema-ok", Severity.OK, "input schema present and typed"))


def _run_case(client: MCPClient, name: str, case, report: Report) -> bool:
    """Return False if the server appears to have CRASHED (connection dead)."""
    try:
        client.call_tool(name, case.args)
        accepted = True
        err = None
    except ToolError as e:
        accepted = False
        err = str(e)[:200]
    except Exception as e:                              # transport died => crash
        report.add(Finding(name, "crash", Severity.FAIL,
                           f"[{case.check}] server crashed / connection lost on this input",
                           {"case": case.check, "error": repr(e)[:200], "note": case.note}))
        return False

    if case.check == "valid":
        if accepted:
            report.add(Finding(name, "valid-baseline", Severity.OK,
                               "accepts a schema-valid argument set"))
        else:
            # A CLEAN rejection of schema-valid input is usually correct behaviour, not a bug:
            # the tool may need a path that exists, an id that resolves, or a combination the
            # schema cannot express. A generic prober cannot know the semantics, so reporting
            # this as a failure manufactures false positives (the flaw that makes most scanners
            # untrustworthy). Only a CRASH is a genuine failure - handled above.
            report.add(Finding(name, "valid-baseline", Severity.INFO,
                               "declined minimal valid input - likely needs semantically real "
                               "values (e.g. an existing path/id), not a defect",
                               {"error": err}))
    elif case.check in ("missing-required", "wrong-type"):
        if accepted:
            report.add(Finding(name, case.check, Severity.WARN,
                               f"accepted clearly-invalid input ({case.note}) - not validating",
                               {"note": case.note}))
        elif err and _UNHANDLED.search(err):
            # rejected, but by an unhandled internal exception rather than input validation
            report.add(Finding(name, "unhandled-error", Severity.WARN,
                               f"crashed internally on invalid input ({case.note}) instead of "
                               f"validating it; the raw error leaks implementation detail",
                               {"note": case.note, "error": err}))
        else:
            report.add(Finding(name, case.check, Severity.OK,
                               f"cleanly rejected invalid input ({case.note})"))
    else:  # soft robustness cases: only a crash matters; survival is OK
        report.add(Finding(name, case.check, Severity.OK,
                           f"survived {case.note}"))
    return True


def probe_server(client: MCPClient, server_label: str, allow_remote: bool = False) -> Report:
    tools = client.list_tools()
    report = Report(server=server_label, tools=tools)
    if not tools:
        report.add(Finding("-", "no-tools", Severity.WARN, "server advertised zero tools"))
        return report

    if not allow_remote:
        probe_target = next((t for t in tools if not t.needs_task_support), None)
        if probe_target is not None:
            evidence = _looks_remote(client, probe_target)
            if evidence:
                raise RemoteBackendDetected(
                    f"'{probe_target.name}' appears to forward to a remote service "
                    f"(saw {evidence!r} in its reply).\n"
                    f"A full run would send roughly {10 * len(tools)} adversarial requests - "
                    f"including 100,000-character strings - to infrastructure that is not yours.\n"
                    f"Audit it only against a service you own or have permission to test, then "
                    f"pass --allow-remote.")

    for spec in tools:
        _schema_hygiene(report, spec)
        if spec.needs_task_support:
            # The tool declares execution.taskSupport = "required": it will refuse every call
            # from a client that lacks task augmentation, including valid ones. Probing it
            # would produce a false "rejected its own valid input". Skip and say so.
            report.add(Finding(spec.name, "skipped-task-support", Severity.INFO,
                               "tool requires client task augmentation; not probed by this "
                               "client (declared execution.taskSupport='required')"))
            continue
        alive = _run_case(client, spec.name, valid_case(spec), report)
        for case in adversarial_cases(spec):
            if not alive:
                break                                   # stop hammering a crashed server
            alive = _run_case(client, spec.name, case, report)
    return report

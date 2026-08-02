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

from .client import MCPClient, ToolError
from .fuzz import adversarial_cases, valid_case
from .model import Finding, Report, Severity, ToolSpec


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
        else:
            report.add(Finding(name, case.check, Severity.OK,
                               f"cleanly rejected invalid input ({case.note})"))
    else:  # soft robustness cases: only a crash matters; survival is OK
        report.add(Finding(name, case.check, Severity.OK,
                           f"survived {case.note}"))
    return True


def probe_server(client: MCPClient, server_label: str) -> Report:
    tools = client.list_tools()
    report = Report(server=server_label, tools=tools)
    if not tools:
        report.add(Finding("-", "no-tools", Severity.WARN, "server advertised zero tools"))
        return report

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

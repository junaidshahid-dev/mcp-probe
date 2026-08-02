"""Schema-driven input generation.

Given a tool's JSON-schema, produce:
  - one VALID argument set (baseline: the server should accept it)
  - a set of INVALID / adversarial argument sets, each targeting one failure mode:
      wrong-type, missing-required, extra-unknown, empty-string, huge-string,
      boundary-number, injection-shaped-string.

A well-built MCP tool validates its inputs and rejects the invalid ones with a clean error
instead of crashing. mcp-probe checks exactly that.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import ToolSpec

HUGE = "A" * 100_000
INJECTION = "'; DROP TABLE users; -- {{7*7}} <script>alert(1)</script> ../../etc/passwd"


@dataclass
class Case:
    check: str            # which failure mode this exercises ("valid" for the baseline)
    args: dict
    expect_accept: bool   # should a correct server accept these args?
    note: str = ""


# Field names whose values must look like something real. Sending "test" as a `path` or `url`
# gets a legitimate rejection that has nothing to do with input validation - the single biggest
# source of false positives in schema-driven fuzzing.
_SEMANTIC_HINTS = (
    (("path", "file", "filepath", "filename", "dir", "directory"), "."),
    (("url", "uri", "endpoint", "webhook"), "https://example.com"),
    (("email", "mail"), "user@example.com"),
    (("date", "datetime", "timestamp"), "2026-01-01"),
    (("query", "search", "q", "text", "message", "content", "prompt"), "test"),
    (("id", "uuid", "key", "token", "name"), "test"),
)


def _valid_value(prop: dict, field_name: str = ""):
    t = prop.get("type", "string")
    if "enum" in prop and prop["enum"]:
        return prop["enum"][0]
    if "default" in prop:
        return prop["default"]
    if t == "string":
        low = field_name.lower()
        for names, value in _SEMANTIC_HINTS:
            if any(n == low or low.endswith("_" + n) or low.startswith(n + "_") for n in names):
                return value
        return "test"
    return {"integer": 1, "number": 1.0, "boolean": True,
            "array": [], "object": {}}.get(t, "test")


def _wrong_typed_value(prop: dict):
    t = prop.get("type", "string")
    # deliberately the wrong python type for the declared schema type
    return {"string": 12345, "integer": "not-an-int", "number": "not-a-number",
            "boolean": "maybe", "array": "not-a-list", "object": "not-an-object"}.get(t, 999)


def valid_case(spec: ToolSpec) -> Case:
    """MINIMAL valid input: required fields only.

    Optional fields are deliberately omitted. Filling them in triggers cross-field constraints
    that JSON Schema cannot express (e.g. filesystem's "cannot specify both head and tail"),
    producing a rejection that looks like a server bug but is correct behaviour.
    """
    args = {name: _valid_value(spec.properties.get(name, {}), name) for name in spec.required}
    return Case("valid", args, expect_accept=True, note="minimal valid input (required fields only)")


def adversarial_cases(spec: ToolSpec) -> list[Case]:
    base = valid_case(spec).args
    cases: list[Case] = []

    # missing each required field, one at a time
    for r in spec.required:
        a = dict(base)
        a.pop(r, None)
        cases.append(Case("missing-required", a, expect_accept=False,
                          note=f"omit required '{r}'"))

    # wrong type for each typed property
    for name, p in spec.properties.items():
        if "type" in p:
            a = dict(base)
            a[name] = _wrong_typed_value(p)
            cases.append(Case("wrong-type", a, expect_accept=False,
                              note=f"'{name}' as wrong type"))

    # extra unknown field (strict servers may reject; lenient ignore — INFO either way)
    a = dict(base)
    a["__unexpected_field__"] = "x"
    cases.append(Case("extra-unknown", a, expect_accept=True,
                      note="unknown extra field (should be ignored or cleanly rejected)"))

    # string stressors on the first string field
    str_field = next((n for n, p in spec.properties.items()
                      if p.get("type", "string") == "string"), None)
    if str_field:
        for check, val, note in [
            ("empty-string", "", "empty string"),
            ("huge-string", HUGE, "100k-char string (DoS / bound check)"),
            ("injection-shaped", INJECTION, "injection-shaped payload (must be treated as data)"),
        ]:
            a = dict(base)
            a[str_field] = val
            # these are 'soft' — a server may legitimately accept or reject; we only
            # require it not to CRASH. expect_accept=None-like via expect_accept=True + soft.
            cases.append(Case(check, a, expect_accept=True, note=f"'{str_field}': {note}"))

    return cases

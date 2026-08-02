"""Core data model for a probe run — the vocabulary everything else speaks."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    OK = "ok"
    INFO = "info"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class Finding:
    tool: str
    check: str                 # short slug, e.g. "wrong-type", "missing-required"
    severity: Severity
    message: str
    detail: dict = field(default_factory=dict)


@dataclass
class ToolSpec:
    """A tool as advertised by an MCP server: name, description, JSON-schema of its input."""
    name: str
    description: str
    input_schema: dict
    execution: dict = field(default_factory=dict)   # e.g. {"taskSupport": "required"}

    @property
    def required(self) -> list[str]:
        return list(self.input_schema.get("required", []))

    @property
    def properties(self) -> dict:
        return self.input_schema.get("properties", {}) or {}

    @property
    def needs_task_support(self) -> bool:
        """True when the tool can only be called by a client that implements task augmentation.

        Such a tool will refuse ANY call from a plain client - including a schema-valid one.
        Probing it without honouring this would report a false 'rejected its own valid input',
        which is a bug report the maintainer would rightly reject.
        """
        return str(self.execution.get("taskSupport", "")).lower() == "required"


@dataclass
class Report:
    server: str
    tools: list[ToolSpec]
    findings: list[Finding] = field(default_factory=list)

    def add(self, f: Finding) -> None:
        self.findings.append(f)

    # ---- scoring: a 0-100 health score, weighted by severity ----
    def counts(self) -> dict[str, int]:
        c = {s.value: 0 for s in Severity}
        for f in self.findings:
            c[f.severity.value] += 1
        return c

    def score(self) -> int:
        c = self.counts()
        penalty = c["fail"] * 15 + c["warn"] * 4 + c["info"] * 0
        return max(0, 100 - penalty)

    def grade(self) -> str:
        s = self.score()
        return "A" if s >= 90 else "B" if s >= 75 else "C" if s >= 60 else "D" if s >= 40 else "F"

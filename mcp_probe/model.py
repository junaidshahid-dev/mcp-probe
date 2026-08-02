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
        """0-100 health score: the MEAN of per-tool scores.

        Scoring each tool then averaging is deliberate. A flat penalty across the whole server
        punishes size - a careful 23-tool server accumulates more findings than a sloppy 2-tool
        one and grades worse despite being better per unit of surface. Averaging asks the right
        question: "what fraction of this server's tools are sound?"

        INFO findings never affect the score; they are observations, not defects.
        """
        if not self.tools:
            return 0 if any(f.severity is Severity.FAIL for f in self.findings) else 100
        per_tool: dict[str, int] = {t.name: 100 for t in self.tools}
        # Tools we could not probe are EXCLUDED from the average rather than counted as
        # perfect: an untested tool is unknown, not sound. Counting it 100 would let a server
        # raise its grade simply by having tools this client cannot exercise.
        skipped = {f.tool for f in self.findings if f.check == "skipped-task-support"}
        for f in self.findings:
            if f.tool not in per_tool:
                continue
            if f.severity is Severity.FAIL:
                per_tool[f.tool] -= 50
            elif f.severity is Severity.WARN:
                per_tool[f.tool] -= 20
        scored = [max(0, v) for name, v in per_tool.items() if name not in skipped]
        return int(round(sum(scored) / len(scored))) if scored else 100

    def grade(self) -> str:
        s = self.score()
        return "A" if s >= 90 else "B" if s >= 75 else "C" if s >= 60 else "D" if s >= 40 else "F"

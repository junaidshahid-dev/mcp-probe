# Audit: the official MCP servers (2026-08)

I ran `mcp-probe` against four official `@modelcontextprotocol` servers to see how the
best-maintained servers in the ecosystem hold up.

## Result

| Server | Tools | Score | Grade |
|---|---|---|---|
| server-memory | 9 | 100/100 | A |
| server-everything | 13 | 100/100 | A |
| server-sequential-thinking | 1 | 100/100 | A |
| server-filesystem | 14 | 100/100 | A |

**All four passed cleanly.** They reject wrong-typed and missing arguments with clean errors,
and survive empty, oversized (100k char) and injection-shaped strings without crashing.

## The interesting part: the first run said they were broken

My initial run scored `server-filesystem` **0/100 (F)** and `server-everything` **85/100**.
Both were **false positives in my own tool.** I investigated instead of publishing, and found
three distinct bugs in mcp-probe:

1. **Ignored `execution.taskSupport`.** Tools declaring `taskSupport: "required"` refuse every
   call from a client without task augmentation - including valid ones. Probing them produced a
   bogus "rejected its own valid input". Such tools are now skipped and reported as INFO.

2. **Filled in optional parameters.** The baseline case sent every parameter, tripping
   cross-field constraints JSON Schema cannot express - filesystem correctly answered
   *"Cannot specify both head and tail parameters simultaneously."* The baseline now sends
   **required fields only**.

3. **Treated semantic rejection as failure.** Sending `path: "test"` to a file tool gets a
   legitimate rejection that says nothing about input validation. Field-name-aware values are
   now generated (`path`, `url`, `email`, `date`...), and a *clean* rejection of valid-shaped
   input is reported as **INFO, not FAIL** - only a crash is a genuine failure.

Independent research puts the false-positive rate of existing MCP scanners at ~78%
(6 genuine findings out of 27 detections). This is that same disease. A scanner that fails
well-built servers is worse than no scanner, because it trains people to ignore it.

## Calibration check

After the fixes, mcp-probe still catches real defects. Re-run against my own MCP server:

```
apex_mcp - score: 62/100 (grade C)
  [FAIL] forward_test_report - crashes on a wrong-typed argument
  [FAIL] search_graveyard    - crashes on a wrong-typed argument
  [WARN] run_orb_backtest    - accepts invalid input without validating (x2)
```

Sensitive to real bugs, quiet on healthy servers. That is the whole job.

## Method

`mcp-probe` connects over stdio, discovers each tool's schema, and generates adversarial inputs
per failure mode: missing required fields, wrong types, unknown extras, empty strings, 100k-char
strings, and injection-shaped payloads. A crash (transport lost) is FAIL; silently accepting
clearly-invalid input is WARN; a clean rejection is correct behaviour.

Reproduce: `python -m mcp_probe.cli --cmd "node path/to/server.js" --markdown report.md`

# Auditing the MCP ecosystem with mcp-probe (2026-08)

Seven real, publicly installable MCP servers audited - four official, three community.

## Results

| Server | Tools | Score | Grade |
|---|---|---|---|
| `@modelcontextprotocol/server-memory` | 9 | 100 | A |
| `@modelcontextprotocol/server-everything` | 13 | 100 | A |
| `@modelcontextprotocol/server-sequential-thinking` | 1 | 100 | A |
| `@modelcontextprotocol/server-filesystem` | 14 | 100 | A |
| `@upstash/context7-mcp` | 2 | 100 | A |
| `@playwright/mcp` | 24 | 97 | A |
| `REDACTED-PENDING-DISCLOSURE` | 23 | **69** | **C** |

The official servers are genuinely well built: they reject wrong-typed and missing arguments
cleanly, and survive empty, 100k-character and injection-shaped strings without crashing.

## The real finding: `REDACTED-PENDING-DISCLOSURE` does not validate its inputs

Called with **no arguments at all**, `REDACTED` did not refuse. It built and executed:

```
REDACTED scale deployment  --replicas=undefined --namespace=default
```

Its own schema declares `name` and `replicas` as required. Neither is enforced; the missing
values are interpolated straight into a shell command. 12 further tools answer invalid input
with an unhandled runtime error rather than validation, e.g.:

```
input.resourceType.toLowerCase is not a function
```

That is not a rejection - it is a crash inside the handler that happens to be caught, and it
leaks implementation detail back to the caller. For a server that shells out to `REDACTED`,
unvalidated input reaching command construction is the wrong default.

*(Reported to the maintainer before publication.)*

## Three false positives - and one false negative - fixed in mcp-probe itself

The first run graded `server-filesystem` **0/100 (F)**. That was wrong, and investigating it
was more valuable than publishing it.

1. **`execution.taskSupport: "required"` ignored.** Such tools refuse every call from a client
   without task augmentation, including valid ones. Now skipped and reported as INFO - and
   *excluded* from the score, because an untested tool is unknown, not sound.
2. **Optional parameters were filled in.** That trips cross-field rules JSON Schema cannot
   express - filesystem correctly answered *"Cannot specify both head and tail parameters
   simultaneously."* The baseline now sends **required fields only**.
3. **Semantic rejection treated as a defect.** `path: "test"` is schema-valid and semantically
   meaningless. Values are now field-name aware (`path`, `url`, `email`, `date`), and a *clean*
   rejection of valid-shaped input is INFO, not FAIL. Only a crash is a genuine failure.
4. **False negative: internal crashes scored as clean validation.** A server answering
   `"is not a function"` did not validate anything. These are now detected and flagged -
   which surfaced 12 findings in REDACTED that the earlier version silently passed.

Independent research puts existing MCP scanners at roughly a **78% false-positive rate**
(6 genuine findings in 27 detections). A scanner that fails well-built servers trains people
to ignore it, so calibration is the product, not a detail.

## Scoring

Each tool is scored, then averaged. A flat per-server penalty punishes size: a careful 23-tool
server accumulates more findings than a sloppy 2-tool one and would grade worse while being
better per unit of surface. Averaging asks the right question - *what fraction of this server's
tools are sound?* FAIL costs 50, WARN costs 20, INFO costs nothing.

Calibration after the fixes: well-built servers score 100, a large server with a few minor gaps
scores 97, a server with real validation gaps across half its tools scores 69 - and my own MCP
server still scores **62 (C)** for two genuine crash bugs. Sensitive to defects, quiet on
healthy code.

## Reproduce

```bash
pip install -r requirements.txt
python -m mcp_probe.cli --cmd "node path/to/server.js" --markdown report.md
```

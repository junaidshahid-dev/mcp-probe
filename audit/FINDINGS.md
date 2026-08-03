# Auditing the MCP ecosystem with mcp-probe

Thirteen real, publicly installable MCP servers audited across two rounds — official servers
from Anthropic, Google, Microsoft and MongoDB, plus community and vendor servers.

## Results

| Server | Maintainer | Tools | Score | Grade |
|---|---|---|---|---|
| `@modelcontextprotocol/server-memory` | Anthropic | 9 | 100 | A |
| `@modelcontextprotocol/server-everything` | Anthropic | 13 | 100 | A |
| `@modelcontextprotocol/server-sequential-thinking` | Anthropic | 1 | 100 | A |
| `@modelcontextprotocol/server-filesystem` | Anthropic | 14 | 100 | A |
| `mcp-server-git` | Anthropic | 12 | 100 | A |
| `mcp-server-time` | Anthropic | 2 | 100 | A |
| `chrome-devtools-mcp` | Google | 29 | 100 | A |
| `markitdown-mcp` | Microsoft | 1 | 100 | A |
| `mongodb-mcp-server` | MongoDB | 29 | 100 | A |
| `@upstash/context7-mcp` | Upstash | 2 | 100 | A |
| `@playwright/mcp` | Microsoft | 24 | 97 | A |
| *(community server, pending disclosure)* | — | 23 | **69** | **C** |
| *(vendor server, pending disclosure)* | — | 27 | **11** | **F** |

The well-resourced servers are genuinely well built. They reject wrong-typed and missing
arguments cleanly and survive empty, 100k-character and injection-shaped strings without
crashing. Two servers have real validation gaps; both have been reported privately through the
maintainer's stated channel and are unnamed here until they have had time to respond.

The spread matters more than any single score. A scanner that flags everything is worthless —
eleven of thirteen scoring 97-100 in the same run as an 11/F is what makes the 11 credible.

---

## An ecosystem finding that needed no fuzzing at all

Three servers **would not start on a fresh install**, including two of Anthropic's own and one
of Microsoft's:

| Package | Declares | pip resolves | Result on startup |
|---|---|---|---|
| `mcp-server-time` | `mcp>=1.23.0` | 2.0.0 | `ImportError: cannot import name 'McpError'` (renamed `MCPError`) |
| `mcp-server-git` | `mcp>=1.0.0` | 2.0.0 | `AttributeError: 'Server' object has no attribute 'list_tools'` |
| `markitdown-mcp` | `mcp` *(unbounded)* | 2.0.0 | `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` |

The Python SDK released 2.0 and removed those APIs. All three declare a lower bound with no
upper bound, so `pip install <server>` today pulls an SDK the server cannot run against. Pinning
`mcp<2` fixes all three, after which each scores 100/A — the code is fine; the packaging is not.

This is the least glamorous class of defect in the ecosystem and probably the most common. It
also costs nothing to check, which is the point.

---

## Two servers pending disclosure

Both have input-validation gaps reported privately via the maintainer's stated security channel.
Details are withheld until they have had a reasonable opportunity to respond. In one case the
server accepts calls with required arguments missing and interpolates the result into a shell
command; in the other, the declared schema is not enforced at any layer and the backend's stack
traces reach the client.

---

## Five false positives, one false negative, and one thing I should not have done

Every one of these was found by running the tool against real servers. None came from writing
tests first.

**Round 1 — the first run graded `server-filesystem` 0/100 (F).** That was wrong, and
investigating it was worth more than publishing it.

1. **`execution.taskSupport: "required"` ignored.** Such tools refuse every call from a client
   without task augmentation, including valid ones. Now skipped as INFO and *excluded* from the
   score, because an untested tool is unknown, not sound.
2. **Optional parameters were filled in.** That trips cross-field rules JSON Schema cannot
   express — filesystem correctly answered *"Cannot specify both head and tail parameters
   simultaneously."* The baseline now sends **required fields only**.
3. **Semantic rejection treated as a defect.** `path: "test"` is schema-valid and semantically
   meaningless. Values are now field-name aware (`path`, `url`, `email`, `date`), and a *clean*
   rejection of valid-shaped input is INFO, not FAIL. Only a crash is a genuine failure.
4. **False negative: internal crashes scored as clean validation.** A server answering
   `"is not a function"` validated nothing — it crashed and the exception happened to be caught.
   Now detected and flagged.

**Round 2 — two transport bugs that stopped audits before they started.**

5. **stdout was decoded with the locale codepage, not UTF-8.** MCP is UTF-8 by specification.
   On a Windows cp1252 console, any server with CJK, emoji or curly-quote tool text killed the
   probe with `UnicodeDecodeError` during `tools/list` — before a single tool was audited. An
   auditor that crashes on a server's valid output is not an auditor.
6. **A server dying at startup reported only `server closed the connection`.** True, and
   useless. `stderr` went to `DEVNULL`, so the traceback holding the entire answer was
   discarded. This is the most common thing a user hits, and it produced the least information.
   stderr is now captured and included in the error — which is how the packaging finding above
   was diagnosed in seconds rather than by guesswork.

**And one judgement error, which belongs here more than any of the above.**

7. **mcp-probe fuzzed somebody else's production API.** One audited server is a thin client for
   a hosted service: every tool call is an outbound HTTPS request to the vendor's backend.
   Auditing it sent roughly 270 adversarial requests — including 100,000-character strings — to
   infrastructure whose owner never agreed to it. Nothing broke, and it was ordinary use of the
   package as published, but "the package did it" is not consent, and I should have thought
   about it before the run rather than after.

   mcp-probe now makes **one** call to the first tool and looks for evidence of a remote backend
   (an external URL, or a container/serverless path such as `/var/task/` in the reply). If it
   finds one it **refuses to continue** and says how many requests it would have sent:

   ```
   refusing to fuzz: 'generate_area_chart' appears to forward to a remote service
   (saw 'https://…' in its reply).
   A full run would send roughly 270 adversarial requests - including 100,000-character
   strings - to infrastructure that is not yours.
   Audit it only against a service you own or have permission to test, then --allow-remote.
   ```

   Detection costs one request instead of 270. `localhost` is explicitly not treated as someone
   else's service, and both behaviours are regression-tested.

Independent research puts existing MCP scanners at roughly a **78% false-positive rate** (6
genuine findings in 27 detections). A scanner that fails well-built servers trains people to
ignore it, so calibration is the product, not a detail — and a scanner that quietly
DoS-tests third parties is a liability to whoever runs it.

---

## Scoring

Each tool is scored, then averaged. A flat per-server penalty punishes size: a careful 29-tool
server accumulates more findings than a sloppy 2-tool one and would grade worse while being
better per unit of surface. Averaging asks the right question — *what fraction of this server's
tools are sound?* FAIL costs 50, WARN costs 20, INFO costs nothing.

Calibration after the fixes: well-built servers score 100, a large server with minor gaps scores
97, a server with validation gaps across half its tools scores 69, a server that validates
nothing scores 11 — and my own MCP server still scores **62 (C)** for two genuine crash bugs.
Sensitive to defects, quiet on healthy code.

## Reproduce

```bash
pip install -r requirements.txt
python -m mcp_probe.cli --cmd "node path/to/server.js" --markdown report.md
```

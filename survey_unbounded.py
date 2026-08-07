"""survey_unbounded.py — find published MCP servers that cannot install on a clean machine.

The failure mode, measured on 13 servers in audit/FINDINGS.md: a package declares the MCP SDK
with a lower bound and NO upper bound. The SDK shipped 2.0 and removed APIs those servers call,
so `pip install <pkg>` today pulls an SDK the server cannot run against, and it dies on startup
with an ImportError that looks nothing like a dependency problem. It only breaks for NEW users -
the maintainer's own machine has the old SDK cached.

This reads PyPI metadata only. It installs nothing, runs nothing, and contacts no server. It is
a metadata survey, not a scan - safe to run against anything.

    python survey_unbounded.py            # survey the default candidate list
    python survey_unbounded.py pkg1 pkg2  # check specific packages
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request

UA = {"User-Agent": "mcp-probe-survey/1.0 (+https://github.com/junaidshahid-dev/mcp-probe)"}
SPEC = re.compile(r"^\s*([A-Za-z0-9._-]+)\s*(\[[^\]]*\])?\s*(.*)$")


def pypi(pkg):
    try:
        req = urllib.request.Request(f"https://pypi.org/pypi/{pkg}/json", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return None if e.code == 404 else None
    except Exception:
        return None


def mcp_constraint(requires_dist):
    """Return the raw specifier string for the `mcp` dependency, or None."""
    for raw in requires_dist or []:
        head = raw.split(";")[0]                      # drop environment markers
        m = SPEC.match(head)
        if not m:
            continue
        if m.group(1).lower().replace("_", "-") == "mcp":
            return m.group(3).strip() or "(any version)"
    return None


def unbounded(spec):
    """True if the specifier permits mcp 2.x — i.e. nothing caps it below 2."""
    if spec is None:
        return False
    if spec == "(any version)":
        return True
    # any of <2, <=1, ==1.x, ~=1.x, <2.0 caps it safely
    for part in [p.strip() for p in spec.split(",")]:
        if part.startswith("<") and not part.startswith("<="):
            return False
        if part.startswith("<="):
            return False
        if part.startswith("=="):
            return False
        if part.startswith("~="):
            return False
    return True


CANDIDATES = [
    # Anthropic reference servers
    "mcp-server-git", "mcp-server-time", "mcp-server-fetch", "mcp-server-sqlite",
    "mcp-server-filesystem", "mcp-server-memory", "mcp-server-sentry",
    # Microsoft / vendor
    "markitdown-mcp", "playwright-mcp", "azure-mcp",
    # widely used community servers
    "mcp-server-sqlite-npx", "mcp-server-postgres", "mcp-server-docker",
    "mcp-server-slack", "mcp-server-notion",
    "mcp-server-obsidian", "mcp-server-youtube", "mcp-server-weather",
    "mcp-server-calculator", "mcp-server-shell", "mcp-server-ssh",
    "mcp-server-jira", "mcp-server-github", "mcp-server-gitlab",
    "mcp-server-elasticsearch", "mcp-server-mongodb", "mcp-server-redis",
    "mcp-server-duckdb", "mcp-server-bigquery", "mcp-server-snowflake",
    "mcp-server-airtable", "mcp-server-stripe", "mcp-server-openapi",
    "mcp-server-rag", "mcp-server-chroma", "mcp-server-qdrant",
    "mcp-server-pinecone", "mcp-server-milvus", "mcp-server-neo4j",
    "mcp-simple-tool", "mcp-python-interpreter", "mcp-code-executor",
    "arxiv-mcp-server", "pubmed-mcp-server", "wikipedia-mcp",
    "yfinance-mcp", "alpaca-mcp", "notion-mcp-server", "todoist-mcp",
    "linear-mcp-server", "sentry-mcp", "grafana-mcp", "prometheus-mcp",
]


def main():
    pkgs = sys.argv[1:] or CANDIDATES
    print("=" * 92)
    print("MCP servers on PyPI whose SDK dependency is not capped below 2.0")
    print("metadata only — nothing installed, nothing executed, no server contacted")
    print("=" * 92)
    print(f"  {'package':<32}{'version':<14}{'mcp constraint':<22}verdict")
    print("-" * 92)
    broken, safe, missing, nodep = [], [], [], []
    for p in pkgs:
        d = pypi(p)
        time.sleep(0.3)                                # be polite to PyPI
        if not d:
            missing.append(p); continue
        info = d["info"]
        spec = mcp_constraint(info.get("requires_dist"))
        if spec is None:
            nodep.append(p); continue
        bad = unbounded(spec)
        (broken if bad else safe).append((p, info["version"], spec))
        print(f"  {p:<32}{info['version']:<14}{'mcp ' + spec:<22}"
              f"{'*** UNBOUNDED — breaks on mcp 2.x' if bad else 'capped, fine'}")
    print("-" * 92)
    print(f"  unbounded: {len(broken)}   capped: {len(safe)}   "
          f"no mcp dep (likely not a Python MCP server): {len(nodep)}   not on PyPI: {len(missing)}")
    if broken:
        print("\n  CANDIDATES TO VERIFY (install each in a clean venv and capture the traceback):")
        for p, v, s in broken:
            print(f"     python -m venv .t && .t\\Scripts\\pip install {p} && .t\\Scripts\\{p}")
    print("\n  NOTE: unbounded metadata is necessary but NOT sufficient. A server may still work")
    print("  on mcp 2.x. Verify with a real clean install before contacting anyone.")


if __name__ == "__main__":
    main()

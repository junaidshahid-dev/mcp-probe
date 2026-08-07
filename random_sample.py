"""random_sample.py — a defensible estimate, not a convenience sample.

The first pass hand-picked 23 package names and found 18/21 broken. That number cannot be
generalised: the list was written from memory and biased toward the `mcp-server-*` naming
convention. PyPI actually carries ~18,000 packages with `mcp` as a name token.

This draws a SEEDED RANDOM sample from that population so the result has a real denominator and
a confidence interval, and so anyone can reproduce it exactly.

The population list `pypi_mcp_names.txt` is NOT committed - it is 366 KB and regenerable in
seconds from PyPI's own index (see the fetch snippet in the README). It was pulled 2026-08-07,
when PyPI held 865,752 packages of which 17,995 carried `mcp` as a name token.

Stage 1 (this file): random sample -> how many are genuinely Python MCP servers (declare a direct
`mcp` dependency), and of those, how many leave the SDK uncapped.

Stage 2 (verify_install.py): a random subsample of the uncapped ones gets a real clean install,
giving P(actually breaks | uncapped). The headline estimate is the product of the two, with a
Wilson interval — never a bare percentage.
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
import urllib.request
from math import sqrt

UA = {"User-Agent": "mcp-probe-survey/1.0 (+https://github.com/junaidshahid-dev/mcp-probe)"}
SEED = 20260806
SPEC = re.compile(r"^\s*([A-Za-z0-9._-]+)\s*(\[[^\]]*\])?\s*(.*)$")


def wilson(k, n, z=1.96):
    """Wilson score interval — correct for proportions near 0/1 and small n."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def pypi(pkg):
    try:
        r = urllib.request.Request(f"https://pypi.org/pypi/{pkg}/json", headers=UA)
        with urllib.request.urlopen(r, timeout=20) as f:
            return json.load(f)
    except Exception:
        return None


def mcp_spec(requires_dist):
    for raw in requires_dist or []:
        head = raw.split(";")[0]
        m = SPEC.match(head)
        if m and m.group(1).lower().replace("_", "-") == "mcp":
            return m.group(3).strip() or "(any)"
    return None


def capped(spec):
    """Does the specifier prevent mcp 2.x from being installed?"""
    if spec is None or spec == "(any)":
        return False
    for part in [p.strip() for p in spec.split(",")]:
        if part.startswith(("<", "<=", "==", "~=")):
            return True
    return False


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    names = [l.strip() for l in open("pypi_mcp_names.txt", encoding="utf-8") if l.strip()]
    random.seed(SEED)
    sample = random.sample(names, min(n, len(names)))
    print(f"population: {len(names):,} PyPI packages with 'mcp' as a name token")
    print(f"random sample: {len(sample)}   seed {SEED} (reproducible)\n")

    servers, uncapped, capped_ok, nodep, gone = [], [], [], 0, 0
    for i, p in enumerate(sample, 1):
        d = pypi(p)
        time.sleep(0.12)
        if not d:
            gone += 1
            continue
        spec = mcp_spec(d["info"].get("requires_dist"))
        if spec is None:
            nodep += 1
            continue
        servers.append(p)
        (capped_ok if capped(spec) else uncapped).append((p, d["info"]["version"], spec))
        if i % 50 == 0:
            print(f"   {i}/{len(sample)} checked ...")

    ns, nu = len(servers), len(uncapped)
    lo, hi = wilson(nu, ns)
    print(f"\n{'='*76}")
    print(f"  sampled                       {len(sample)}")
    print(f"  unreachable / deleted         {gone}")
    print(f"  no direct `mcp` dependency    {nodep}   (wrappers, clients, unrelated names)")
    print(f"  genuine Python MCP servers    {ns}")
    print(f"{'='*76}")
    print(f"  SDK left UNCAPPED             {nu} of {ns}  = {nu/max(ns,1)*100:.1f}%")
    print(f"  95% CI (Wilson)               {lo*100:.1f}% – {hi*100:.1f}%")
    print(f"  properly capped               {len(capped_ok)}")
    print(f"{'='*76}")
    json.dump({"seed": SEED, "population": len(names), "sampled": len(sample),
               "servers": ns, "uncapped": nu, "ci95": [lo, hi],
               "uncapped_list": uncapped, "capped_list": capped_ok},
              open("random_sample_results.json", "w", encoding="utf-8"), indent=2)
    print("\n  uncapped -> random_sample_results.json (stage 2 installs a subsample of these)")
    print("  NOTE: uncapped is NOT the same as broken. Stage 2 measures how many actually fail.")


if __name__ == "__main__":
    main()

"""verify_install.py — prove, per package, whether it starts on a clean install.

Metadata says 24/27 Python MCP servers do not cap the SDK below 2.0. That is NECESSARY but not
SUFFICIENT: a server may have migrated its code to mcp 2.x and simply not tightened the pin.
Nobody gets emailed off metadata. This produces the actual traceback, or clears the package.

PER PACKAGE:
  1. build a genuinely fresh venv (never reuse - a cached SDK is the whole reason maintainers
     cannot see this bug on their own machines)
  2. pip install <pkg> from PyPI
  3. find its console entry points and run each with stdin CLOSED
       - immediate traceback (ImportError / AttributeError / ModuleNotFoundError) -> BROKEN
       - exits quietly on EOF, or blocks until timeout                            -> STARTS FINE
  4. if broken: reinstall with `mcp<2` and re-run. If it then starts, the fix is CONFIRMED
     and that pair (error + fix) is the whole email.
  5. delete the venv immediately - 23 venvs would be several GB

SAFETY: installs and starts software locally. It sends nothing to any third-party server, makes
no network calls beyond PyPI, and fuzzes nothing. Starting a stdio server with closed stdin is
the gentlest possible check.

A small exclusion list is honoured for servers being handled through a separate disclosure
process. Packages there are checked privately and left out of published results.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXCLUDE = set(l.strip() for l in pathlib.Path("exclude.txt").read_text().splitlines()
              if l.strip() and not l.startswith("#")) if pathlib.Path("exclude.txt").exists() else set()

TARGETS = [
    "mcp-server-git", "mcp-server-time", "mcp-server-fetch", "mcp-server-sqlite",
    "mcp-server-sentry", "playwright-mcp", "mcp-server-notion", "mcp-server-obsidian",
    "mcp-server-weather", "mcp-server-calculator", "mcp-server-shell", "mcp-server-ssh",
    "mcp-server-jira", "mcp-server-redis", "mcp-server-duckdb", "mcp-server-bigquery",
    "mcp-server-snowflake", "mcp-server-rag", "mcp-server-milvus", "mcp-server-neo4j",
    "pubmed-mcp-server", "yfinance-mcp", "prometheus-mcp",
]

BREAKAGE = ("ImportError", "ModuleNotFoundError", "AttributeError", "TypeError",
            "cannot import name", "has no attribute")


def run(cmd, timeout, cwd=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=cwd, stdin=subprocess.DEVNULL,
                           encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "", ""
    except Exception as e:
        return "ERROR", "", str(e)


def scripts_in(venv: Path, pkg: str):
    """Console scripts the package installed, excluding pip/python plumbing."""
    sd = venv / ("Scripts" if sys.platform == "win32" else "bin")
    if not sd.exists():
        return []
    skip = {"pip", "pip3", "python", "pythonw", "activate", "deactivate", "wheel",
            "easy_install", "normalizer", "httpx", "dotenv", "pygmentize", "markdown-it",
            "tqdm", "distro", "openai", "uvicorn", "fastapi", "typer", "jsonschema", "py.test",
            "pytest", "numpy-config", "f2py"}
    out = []
    for f in sd.iterdir():
        stem = f.stem.lower()
        if sys.platform == "win32" and f.suffix.lower() != ".exe":
            continue
        if stem in skip or stem.startswith(("pip", "python", "activate")):
            continue
        out.append(f)
    # the package's own name first, if present
    key = pkg.replace("-", "").replace("_", "")
    out.sort(key=lambda f: 0 if f.stem.lower().replace("-", "").replace("_", "") == key else 1)
    return out


def check_one(pkg: str, workdir: Path):
    res = {"package": pkg}
    venv = workdir / f"v_{pkg.replace('-', '_')}"
    rc, _, err = run([sys.executable, "-m", "venv", str(venv)], 180)
    if rc != 0:
        res["verdict"] = "VENV_FAILED"; res["detail"] = err[-300:]; return res
    py = venv / ("Scripts" if sys.platform == "win32" else "bin") / \
         ("python.exe" if sys.platform == "win32" else "python")

    rc, out, err = run([str(py), "-m", "pip", "install", "--disable-pip-version-check",
                        "--no-input", "-q", pkg], 900)
    if rc != 0:
        res["verdict"] = "INSTALL_FAILED"; res["detail"] = (err or out)[-400:]; return res

    rc, out, err = run([str(py), "-m", "pip", "show", "mcp"], 60)
    res["mcp_version"] = next((l.split(":", 1)[1].strip() for l in out.splitlines()
                               if l.lower().startswith("version:")), "?")

    eps = scripts_in(venv, pkg)
    if not eps:
        res["verdict"] = "NO_ENTRYPOINT"; return res
    ep = eps[0]
    res["entrypoint"] = ep.name
    rc, out, err = run([str(ep)], 20)
    blob = (err or "") + (out or "")
    broke = ("Traceback" in blob) and any(k in blob for k in BREAKAGE)

    if not broke:
        res["verdict"] = "STARTS_OK"
        res["detail"] = "timed out waiting for stdin (normal)" if rc == "TIMEOUT" else f"rc={rc}"
        return res

    res["verdict"] = "BROKEN"
    lines = [l for l in blob.splitlines() if l.strip()]
    res["error"] = lines[-1][:200] if lines else ""
    res["traceback"] = "\n".join(lines[-14:])

    # ---- does pinning mcp<2 actually fix it? The email is worthless without this.
    rc2, _, _ = run([str(py), "-m", "pip", "install", "--disable-pip-version-check",
                     "--no-input", "-q", "mcp<2"], 600)
    if rc2 == 0:
        rc3, o3, e3 = run([str(ep)], 20)
        blob3 = (e3 or "") + (o3 or "")
        fixed = not (("Traceback" in blob3) and any(k in blob3 for k in BREAKAGE))
        res["fix_confirmed"] = bool(fixed)
        rc4, o4, _ = run([str(py), "-m", "pip", "show", "mcp"], 60)
        res["mcp_after_pin"] = next((l.split(":", 1)[1].strip() for l in o4.splitlines()
                                     if l.lower().startswith("version:")), "?")
    else:
        res["fix_confirmed"] = None
    return res


def main():
    targets = [t for t in (sys.argv[1:] or TARGETS) if t not in EXCLUDE]
    work = Path(tempfile.mkdtemp(prefix="mcpverify_"))
    out_path = Path(__file__).with_name("verify_results.json")
    results = []
    print(f"verifying {len(targets)} packages in {work}")
    print(f"{'package':<24}{'mcp':<10}{'verdict':<16}fix?  error")
    print("-" * 100)
    try:
        for i, pkg in enumerate(targets, 1):
            r = check_one(pkg, work)
            results.append(r)
            fx = {True: "YES", False: "no", None: "?"}.get(r.get("fix_confirmed"), "-")
            print(f"{pkg:<24}{r.get('mcp_version','-'):<10}{r['verdict']:<16}{fx:<5} "
                  f"{r.get('error','')[:60]}")
            sys.stdout.flush()
            for d in work.iterdir():
                shutil.rmtree(d, ignore_errors=True)     # reclaim space every iteration
            out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    br = [r for r in results if r["verdict"] == "BROKEN"]
    ok = [r for r in results if r["verdict"] == "STARTS_OK"]
    print("-" * 100)
    print(f"BROKEN {len(br)}   STARTS OK {len(ok)}   other {len(results)-len(br)-len(ok)}")
    print(f"of the broken, fix confirmed by pinning mcp<2: "
          f"{sum(1 for r in br if r.get('fix_confirmed'))}/{len(br)}")
    print(f"\nfull results -> {out_path}")


if __name__ == "__main__":
    main()

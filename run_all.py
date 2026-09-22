#!/usr/bin/env python3
"""Run the whole catalog as one suite.

    python run_all.py              every app's tests
    python run_all.py --demos      also re-record demos and check byte-stability
    python run_all.py --quiet      summary only

Exits non-zero if anything fails, so CI can depend on it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APPS = ROOT / "apps"
RAN = re.compile(r"Ran (\d+) test")


def claims() -> dict:
    data = json.loads((ROOT / "claims.json").read_text(encoding="utf-8"))
    return {a["name"]: a for a in data["apps"]}


def run_tests(app: Path) -> tuple[bool, int, str]:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-p", "test_*.py"],
        cwd=app, capture_output=True, text=True,
    )
    output = result.stdout + result.stderr
    match = RAN.search(output)
    count = int(match.group(1)) if match else 0
    return result.returncode == 0, count, output


def rerecord(app: Path) -> tuple[bool, str]:
    """Re-record the demo and report whether the recording changed.

    A recording that churns cannot be diffed in review, so instability is a
    failure here rather than a curiosity.
    """
    trace = app / "demo.json"
    before = hashlib.sha256(trace.read_bytes()).hexdigest() if trace.exists() else None
    result = subprocess.run([sys.executable, "demo.py"], cwd=app,
                            capture_output=True, text=True)
    if result.returncode != 0:
        return False, (result.stderr.strip().splitlines() or ["demo.py failed"])[-1]
    after = hashlib.sha256(trace.read_bytes()).hexdigest()
    if before is not None and before != after:
        return False, "recording changed on re-run"
    return True, ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demos", action="store_true",
                        help="also re-record demos and check byte-stability")
    parser.add_argument("--quiet", action="store_true", help="summary only")
    args = parser.parse_args(argv)

    known = claims()
    apps = sorted(p for p in APPS.iterdir() if p.is_dir())

    failures, total_tests = [], 0
    undocumented = [p.name for p in apps if p.name not in known]

    for app in apps:
        ok, count, output = run_tests(app)
        total_tests += count
        status = "ok  " if ok else "FAIL"

        if ok and args.demos:
            stable, why = rerecord(app)
            if not stable:
                ok, status = False, "DEMO"
                output = why

        if not ok:
            failures.append((app.name, output))
        if not args.quiet:
            claim = known.get(app.name, {}).get("claim", "(not in claims.json)")
            print(f"  {status}  {app.name:<36} {count:>3} tests  {claim[:72]}")

    print()
    print(f"{len(apps) - len(failures)}/{len(apps)} apps passed, {total_tests} tests")

    if undocumented:
        print(f"\nnot in claims.json: {', '.join(undocumented)}")

    for name, output in failures:
        print(f"\n--- {name} ---\n{output.strip()[-1500:]}")

    return 1 if failures or undocumented else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

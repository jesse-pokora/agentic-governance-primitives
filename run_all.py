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
COMPOSITIONS = ROOT / "compositions"
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
    failure here rather than a curiosity. A directory with no demo.py has
    nothing to re-record and is not a failure.
    """
    if not (app / "demo.py").exists():
        return True, ""
    trace = app / "demo.json"
    before = trace.read_text(encoding="utf-8").splitlines() if trace.exists() else None
    result = subprocess.run([sys.executable, "demo.py"], cwd=app,
                            capture_output=True, text=True)
    if result.returncode != 0:
        return False, (result.stderr.strip().splitlines() or ["demo.py failed"])[-1]
    if before is None:
        return True, ""

    after = trace.read_text(encoding="utf-8").splitlines()
    if before == after:
        return True, ""

    # Say what changed. "Recording changed on re-run" with no detail is
    # unhelpful precisely when it fires — on someone else's operating system,
    # where you cannot reproduce it by hand.
    for number, (was, now) in enumerate(zip(before, after), start=1):
        if was != now:
            return False, (
                f"recording changed on re-run, first at line {number}\n"
                f"    was: {was.strip()[:160]}\n"
                f"    now: {now.strip()[:160]}"
            )
    return False, (
        f"recording changed on re-run: {len(before)} lines became {len(after)}"
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demos", action="store_true",
                        help="also re-record demos and check byte-stability")
    parser.add_argument("--quiet", action="store_true", help="summary only")
    args = parser.parse_args(argv)

    known = claims()
    apps = sorted(p for p in APPS.iterdir() if p.is_dir())
    # Compositions are not primitives and carry no claims.json entry. They are
    # run because they exercise the real modules, and a composition breaking is
    # how you find out that two apps stopped fitting together.
    compositions = sorted(p for p in COMPOSITIONS.iterdir() if p.is_dir())         if COMPOSITIONS.exists() else []

    failures, total_tests = [], 0
    undocumented = [p.name for p in apps if p.name not in known]

    for app in apps + compositions:
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
            claim = known.get(app.name, {}).get("claim", "(composition)")
            print(f"  {status}  {app.name:<36} {count:>3} tests  {claim[:72]}")

    print()
    total = len(apps) + len(compositions)
    print(f"{total - len(failures)}/{total} suites passed "
          f"({len(apps)} apps, {len(compositions)} compositions), {total_tests} tests")

    if undocumented:
        print(f"\nnot in claims.json: {', '.join(undocumented)}")

    for name, output in failures:
        print(f"\n--- {name} ---\n{output.strip()[-1500:]}")

    return 1 if failures or undocumented else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

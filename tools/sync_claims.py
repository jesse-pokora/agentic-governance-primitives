#!/usr/bin/env python3
"""Refresh the derived fields in claims.json from each app's recorded demo.

    python tools/sync_claims.py           refresh derived fields
    python tools/sync_claims.py --check   fail if claims.json is stale

Each app entry has two kinds of field. Derived ones -- claim, enforcement,
denial_type, modules, tests, demo_steps -- are read back from the app's demo
recording, which was itself produced by running the real module. Authored ones
-- tier, release, asi, nist, iso, strength -- are judgments and are never
invented here.

An app with no entry is reported rather than guessed at, so adding an app tells
you exactly which judgments are still owed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "claims.json"

DERIVED = ("claim", "enforcement", "denial_type", "modules", "tests", "demo_steps")
AUTHORED = ("tier", "release", "asi", "nist", "iso", "strength", "criticality")


def derived_fields(app_dir: Path) -> dict:
    demo = json.loads((app_dir / "demo.json").read_text(encoding="utf-8"))
    return {
        "claim": demo["claim"],
        "enforcement": demo["enforcement"],
        "denial_type": demo["denial_type"],
        "modules": sorted(
            p.name for p in app_dir.glob("*.py")
            if not p.name.startswith("test_") and p.name != "demo.py"
        ),
        "tests": sorted(p.name for p in app_dir.glob("test_*.py")),
        "demo_steps": len(demo["steps"]),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero if claims.json is stale or incomplete")
    args = parser.parse_args(argv)

    data = json.loads(CLAIMS.read_text(encoding="utf-8"))
    entries = {a["name"]: a for a in data["apps"]}
    app_dirs = {p.name: p for p in sorted((ROOT / "apps").iterdir()) if p.is_dir()}

    missing = sorted(set(app_dirs) - set(entries))
    orphaned = sorted(set(entries) - set(app_dirs))
    incomplete = {
        name: [f for f in AUTHORED if not entry.get(f) and entry.get(f) != []]
        for name, entry in entries.items()
        if any(f not in entry for f in AUTHORED)
    }

    changed = []
    for name, app_dir in app_dirs.items():
        entry = entries.get(name)
        if entry is None:
            continue
        fresh = derived_fields(app_dir)
        if any(entry.get(k) != v for k, v in fresh.items()):
            changed.append(name)
            entry.update(fresh)

    problems = []
    if missing:
        problems.append("no entry in claims.json (add the authored fields): "
                        + ", ".join(missing))
    if orphaned:
        problems.append("entry with no app directory: " + ", ".join(orphaned))
    for name, fields in incomplete.items():
        problems.append(f"{name} is missing authored fields: {', '.join(fields)}")

    if args.check:
        for problem in problems:
            print(problem)
        if changed:
            print("derived fields are stale for: " + ", ".join(changed))
            print("run: python tools/sync_claims.py")
        if problems or changed:
            return 1
        print(f"claims.json is in sync ({len(entries)} apps)")
        return 0

    for problem in problems:
        print(problem)
    if changed:
        data["apps"] = sorted(entries.values(), key=lambda a: a["name"])
        # Explicit LF: claims.json is committed and compared, so it must not
        # depend on which platform last refreshed it.
        with open(CLAIMS, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print("refreshed derived fields for: " + ", ".join(changed))
    else:
        print(f"claims.json already in sync ({len(entries)} apps)")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

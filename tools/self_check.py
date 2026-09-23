#!/usr/bin/env python3
"""Run the catalog's own detectors over the catalog.

    python tools/self_check.py

Every app here is demonstrated against toy fixtures, which is the right way to
prove a claim and a poor way to find out whether the detector survives real
code. This points `structural-duplicate-detection` at all 59 apps and reports
what it finds.

It reports; it does not gate. Duplication in this catalog is frequently
deliberate — every app is standalone and imports nothing from its siblings, so
a shared idiom appears once per app on purpose. The point is to see the list
and decide, not to have a number go green.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "structural-duplicate-detection"))

from fingerprint import duplicates, fingerprints  # noqa: E402


def app_modules() -> list[tuple[str, Path]]:
    """Every shipped module, excluding tests and demo recorders."""
    found = []
    for parent in ("apps", "compositions"):
        for app_dir in sorted((ROOT / parent).iterdir()):
            if not app_dir.is_dir():
                continue
            for module in sorted(app_dir.glob("*.py")):
                if module.name.startswith("test_") or module.name == "demo.py":
                    continue
                found.append((app_dir.name, module))
    return found


def main() -> int:
    modules = app_modules()
    sources = {}
    owners: dict[str, str] = {}

    total_functions = 0
    for app, module in modules:
        text = module.read_text(encoding="utf-8")
        sources[f"{app}/{module.name}"] = text
        for item in fingerprints(text):
            owners[f"{item.fingerprint}:{item.name}:{item.line}"] = app
            total_functions += 1

    groups = duplicates(*sources.values())

    print(f"{len(modules)} modules, {total_functions} functions\n")
    print(f"{len(groups)} group(s) of structurally identical functions:\n")

    for group in groups:
        names = Counter(item.name for item in group)
        shape = "same name" if len(names) == 1 else f"{len(names)} names"
        print(f"  {len(group)} copies, {shape}: "
              f"{', '.join(sorted(set(item.name for item in group)))}")

    duplicated = sum(len(g) for g in groups)
    print(f"\n{duplicated} of {total_functions} functions have at least one twin.")
    print("Deliberate repetition is expected: every app is standalone and "
          "imports nothing from its siblings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

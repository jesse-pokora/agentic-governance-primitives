#!/usr/bin/env python3
"""Regenerate the catalog tables in README.md and CONFORMANCE.md from claims.json.

    python tools/generate_docs.py           rewrite the managed regions
    python tools/generate_docs.py --check   fail if they are out of date

claims.json is the single source of truth for every app's claim, tier, release,
enforcement class and standards mapping. Hand-maintaining those facts across
three documents and 43 apps is a drift surface with no upside; the documents
now hold a generated region instead.

The write goes through this repo's own managed-block-confinement app, so the
prose around each table is human-authored and stays byte for byte as written.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "managed-block-confinement"))

from managed_block import render_managed  # noqa: E402

RELEASES = [
    ("v1", None),
    ("v1.1", "### v1.1 — gap closure\n\nDerived from this catalog's own criteria rather than observed in a source\nsystem: each closes a gap the v1 apps leave open."),
    ("v1.2", "### v1.2 — model-behavior constraint & drift detection\n\nReliability rather than security: the deterministic gates a nondeterministic\nmodel is wrapped in, so its output becomes predictable."),
    ("v1.3", "### v1.3 — derived from an atomic instruction and test matrix\n\nFound by reading a 192-criterion instruction-adherence matrix for one real\ngoverned agent and asking which of its themes had no teaching app here."),
]

TIER_TITLES = {
    1: "Tier 1 — Deterministic security primitives",
    2: "Tier 2 — Review & process governance",
    3: "Tier 3 — Persona & agent architecture",
    4: "Tier 4 — Domain example",
    5: "Tier 5 — Model-behavior constraint & drift detection",
}


def load() -> list[dict]:
    return json.loads((ROOT / "claims.json").read_text(encoding="utf-8"))["apps"]


def status_tables(apps: list[dict]) -> str:
    out = []
    for release, heading in RELEASES:
        rows = [a for a in apps if a["release"] == release]
        if not rows:
            continue
        if heading:
            out.append("\n" + heading + "\n")
        out.append("| App | Enforcement | Status |")
        out.append("|---|---|---|")
        for a in sorted(rows, key=lambda x: (x["tier"], x["name"])):
            out.append(f"| [{a['name']}](apps/{a['name']}) | {a['enforcement']} | built |")
        out.append("")
    return "\n".join(out).strip("\n")


def mapping_tables(apps: list[dict]) -> str:
    out = []
    for tier in sorted({a["tier"] for a in apps}):
        out.append(f"\n### {TIER_TITLES[tier]}\n")
        out.append("| App | OWASP ASI (2026) | NIST SP 800-53 Rev 5 | ISO/IEC 42001 Annex A | Strength |")
        out.append("|---|---|---|---|---|")
        for a in sorted((x for x in apps if x["tier"] == tier), key=lambda x: x["name"]):
            asi = ", ".join(a["asi"]) if a["asi"] else "—"
            out.append(
                f"| {a['name']} | {asi} | {', '.join(a['nist'])} | "
                f"{', '.join(a['iso'])} | {a['strength']} |"
            )
        out.append("")
    return "\n".join(out).strip("\n")


TARGETS = {
    "README.md": status_tables,
    "CONFORMANCE.md": mapping_tables,
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero if a document is out of date")
    args = parser.parse_args(argv)

    apps = load()
    stale = []

    for filename, build in TARGETS.items():
        path = ROOT / filename
        with open(path, "r", encoding="utf-8", newline="") as handle:
            current = handle.read()
        # Match the document's prevailing line ending. managed-block-confinement
        # preserves everything outside the markers byte for byte; emitting LF
        # inside a CRLF document would leave the file mixed, and --check would
        # then report drift forever.
        newline = "\r\n" if "\r\n" in current else "\n"
        body = build(apps).replace("\n", newline)
        updated = render_managed(current, body)
        if current == updated:
            continue
        if args.check:
            stale.append(filename)
        else:
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(updated)
            print(f"regenerated the managed region in {filename}")

    if args.check:
        if stale:
            print("out of date with claims.json: " + ", ".join(stale))
            print("run: python tools/generate_docs.py")
            return 1
        print(f"{len(TARGETS)} documents are in sync with claims.json "
              f"({len(apps)} apps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

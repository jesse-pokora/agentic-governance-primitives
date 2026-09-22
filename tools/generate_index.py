#!/usr/bin/env python3
"""Generate index.html: the catalog's front door.

    python tools/generate_index.py           write index.html
    python tools/generate_index.py --check   fail if it is out of date

Everything on the page comes from claims.json, except the reading path below,
which is a teaching judgment and is written here on purpose. A generated list
of 47 apps is a directory; the order to read them in is the part that makes it
a curriculum, and that cannot be derived from metadata.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "index.html"

# Five apps, in the order they teach best. Four refusals and then the restraint,
# because a reader who meets only the refusals learns half the craft.
READING_PATH = [
    ("hash-pinned-identity",
     "The whole idea in its simplest form: name exactly what may run, refuse "
     "everything else. A byte-identical impostor in another directory is still "
     "refused."),
    ("exact-plan-approval-gate",
     "Consent has to name what it consents to. A “yes” with no hash is not an "
     "approval, and an approval does not survive an edit to the plan."),
    ("authenticated-transition-ledger",
     "Evidence that cannot be quietly corrected. One edited byte anywhere in "
     "history is detected — and a careful attacker who recomputes the hash "
     "still cannot forge the signature."),
    ("capability-gated-tool-invocation",
     "Authorization at the call site, not in the audit afterwards. The denied "
     "tool’s body is never entered, and the test proves it by counting."),
    ("optional-input-does-not-block",
     "The counterweight, and the one most catalogs never teach. After four "
     "refusals, the discipline of not refusing: a run starts on a bare prompt, "
     "because blocking on context you never needed is its own failure."),
]

TIER_TITLES = {
    1: "Deterministic security primitives",
    2: "Review &amp; process governance",
    3: "Persona &amp; agent architecture",
    4: "Domain example",
    5: "Model-behavior constraint &amp; drift detection",
}

CRITICALITY_NOTE = {
    "C0": "unauthorized action becomes possible, or its evidence is destroyed",
    "C1": "governance degrades, or a fact an auditor needs is hidden",
    "C2": "correctness or predictability suffers; authority is intact",
    "C3": "a convention whose violation costs clarity",
}


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def card(app: dict, why: str = "") -> str:
    name = esc(app["name"])
    return f"""      <article class="app">
        <div class="head">
          <a class="name" href="apps/{name}/demo.html">{name}</a>
          <span class="chip {esc(app['criticality'])}" title="{esc(CRITICALITY_NOTE[app['criticality']])}">{esc(app['criticality'])}</span>
          <span class="enf">{esc(app['enforcement'])}</span>
        </div>
        <p class="claim">{esc(app['claim'])}</p>
        {f'<p class="why">{esc(why)}</p>' if why else ''}
        <div class="links">
          <a href="apps/{name}/demo.html">run the demo</a>
          <a href="apps/{name}/README.md">read the claim</a>
        </div>
      </article>"""


def build(apps: list[dict]) -> str:
    by_name = {a["name"]: a for a in apps}

    start = "\n".join(card(by_name[n], why) for n, why in READING_PATH)

    tiers = []
    for tier in sorted({a["tier"] for a in apps}):
        rows = sorted(
            (a for a in apps if a["tier"] == tier),
            key=lambda a: (["C0", "C1", "C2", "C3"].index(a["criticality"]), a["name"]),
        )
        cards = "\n".join(card(a) for a in rows)
        tiers.append(
            f'    <section>\n      <h3>Tier {tier} &middot; {TIER_TITLES[tier]} '
            f'<span class="count">{len(rows)}</span></h3>\n{cards}\n    </section>'
        )

    template = (ROOT / "tools" / "index_template.html").read_text(encoding="utf-8")
    return (
        template.replace("__TOTAL__", str(len(apps)))
        .replace("__START__", start)
        .replace("__TIERS__", "\n".join(tiers))
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    apps = json.loads((ROOT / "claims.json").read_text(encoding="utf-8"))["apps"]
    missing = [n for n, _ in READING_PATH if n not in {a["name"] for a in apps}]
    if missing:
        print("reading path names apps that do not exist: " + ", ".join(missing))
        return 1

    page = build(apps)
    current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""

    if args.check:
        if current != page:
            print("index.html is out of date; run: python tools/generate_index.py")
            return 1
        print(f"index.html is in sync with claims.json ({len(apps)} apps)")
        return 0

    OUT.write_text(page, encoding="utf-8")
    print(f"wrote index.html ({len(apps)} apps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

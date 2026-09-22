"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from replay import Event, ReplayableLedger, replay  # noqa: E402

EVENTS = [
    Event("assign_reviewer", {"persona": "toy-reviewer"}),
    Event("open_finding", {"id": "F-002"}),
    Event("open_finding", {"id": "F-001"}),
    Event("resolve_finding", {"id": "F-002"}),
]


def fresh():
    ledger = ReplayableLedger()
    for e in EVENTS:
        ledger.append(e)
    return ledger


def build() -> Trace:
    t = Trace(
        app="deterministic-ledger-replay",
        claim=(
            "Replaying a ledger from genesis reproduces its state byte-for-byte, and any "
            "state the replay cannot reproduce is rejected — with the first divergent "
            "event named."
        ),
        enforcement="deterministic",
        denial_type="ReplayRejected",
    )
    ledger = fresh()
    t.allow("four events, replayed from genesis",
            {"events": "assign_reviewer, open F-002, open F-001, resolve F-002"},
            lambda: ledger.verify().digest[:24] + "...",
            evidence=lambda: "replayed state equals live state, byte for byte")

    a, b = replay([EVENTS[0]]), replay([Event("assign_reviewer", {"persona": "other"})])
    t.allow("the same events in a different order are a different state",
            {"order A": "reviewer=toy-reviewer", "order B": "reviewer=other"},
            lambda: f"{a.digest[:12]}... vs {b.digest[:12]}...",
            note="Order is part of the state, so 'same events' never implies "
                 "'same state'.")

    bypassed = fresh()
    bypassed.state["open_findings"] = bypassed.state["open_findings"] + ["F-999"]
    t.deny("a write that bypassed the log entirely",
           {"mutation": "state['open_findings'] += ['F-999']", "events": "unchanged"},
           bypassed.verify,
           note="Nothing in the log is wrong, because the change was never in the log. "
                "A tamper-evident log cannot see this; a replay can.")

    tampered = fresh()
    tampered.entries[1] = replace(tampered.entries[1], state_digest_after="f" * 64)
    t.deny("a recorded checkpoint the replay disagrees with",
           {"edited": "entries[1].state_digest_after"},
           tampered.verify,
           evidence=lambda: "pinpointed to the first divergent index, not just 'invalid'")

    t.deny("an event type no reducer recognizes",
           {"events": "assign_reviewer, quietly_close_everything"},
           lambda: replay([EVENTS[0], Event("quietly_close_everything", {})]),
           note="Skipping unrecognized events forks state away from the log that is "
                "supposed to explain it, and the fork grows every schema change.")
    return t


if __name__ == "__main__":
    main(build, __file__)

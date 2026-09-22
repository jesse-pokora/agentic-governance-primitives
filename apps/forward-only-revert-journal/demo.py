"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from revert_journal import ForwardOnlyRevertJournal  # noqa: E402

V1, V2, V3 = "a" * 64, "b" * 64, "c" * 64


def fresh():
    j = ForwardOnlyRevertJournal()
    j.set_state(V1)
    j.set_state(V2)
    return j


def build() -> Trace:
    journal = fresh()
    t = Trace(
        app="forward-only-revert-journal",
        claim=(
            "A revert is recorded as a new forward record naming the state it left "
            "behind, so the abandoned state stays readable and a rewritten history is "
            "detected."
        ),
        enforcement="deterministic",
        denial_type="JournalRejected",
    )
    t.allow("reverting to a state that previously held",
            {"in effect": "b… (v2)", "revert to": "a… (v1)", "history": "set v1, set v2"},
            lambda: journal.revert_to(V1) and "recorded as record 2",
            evidence=lambda: f"records: {[r.kind for r in journal.records]}; "
                             f"abandoned state still in history: "
                             f"{V2 in journal.digests_that_held()}",
            note="A destructive revert deletes exactly the evidence an auditor came "
                 "for — that the system was once in that state, and someone left it.")
    t.deny("reverting to a state the system was never in",
           {"in effect": "a… (v1)", "revert to": "c… (never held)"},
           lambda: journal.revert_to(V3),
           note="A revert to something that never held is a new state wearing the word "
                "revert.")
    truncated = fresh()
    truncated.revert_to(V1)
    del truncated.records[1]
    t.deny("a record deleted from the middle of the history",
           {"records": "3 written, 1 removed", "check": "verify()"},
           truncated.verify,
           evidence=lambda: "index contiguity breaks at the removal point")
    rewritten = fresh()
    rewritten.revert_to(V1)
    rewritten.records[1] = replace(rewritten.records[1], digest=V3)
    t.deny("a record rewritten in place, indices left contiguous",
           {"edited": "records[1].digest", "indices": "still 0, 1, 2"},
           rewritten.verify,
           evidence=lambda: "each record names what was in effect before it, so the "
                            "linkage to the next record no longer holds")
    return t


if __name__ == "__main__":
    main(build, __file__)

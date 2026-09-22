"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from slot_ledger import TypedLedgerSlots, digest_of  # noqa: E402

GEN1 = {"decision": "approved", "by": "toy-reviewer", "generation": 1}
GEN2 = {"decision": "approved", "by": "toy-reviewer", "generation": 2}
GEN3 = {"decision": "revoked", "by": "toy-reviewer", "generation": 3}


def build() -> Trace:
    slots = TypedLedgerSlots()
    first = slots.create("approval/svc-fake-a", GEN1)
    t = Trace(
        app="typed-ledger-slot-supersession",
        claim=(
            "A later record can only replace an earlier one by naming that exact slot key "
            "and the exact digest of the record it's replacing — a fork or missing "
            "predecessor fails closed."
        ),
        enforcement="deterministic",
        denial_type="SupersessionDenied",
    )
    t.allow("superseding while naming the exact predecessor digest",
            {"slot": "approval/svc-fake-a", "predecessor": digest_of(GEN1)[:20] + "...",
             "new value": "generation 2"},
            lambda: slots.supersede("approval/svc-fake-a", digest_of(GEN1), GEN2),
            evidence=lambda: "the chain of custody for this slot is unbroken")
    t.deny("superseding with a digest that never held the slot",
           {"slot": "approval/svc-fake-a", "predecessor named": digest_of(GEN3)[:20] + "...",
            "actually holds": "generation 2"},
           lambda: slots.supersede("approval/svc-fake-a", digest_of(GEN3), GEN3),
           note="Naming the wrong predecessor is a fork: two records claiming to "
                "replace the same thing.")
    t.deny("re-using the original digest after it was already superseded",
           {"slot": "approval/svc-fake-a", "predecessor named": digest_of(GEN1)[:20] + "...",
            "generation": "stale by one"},
           lambda: slots.supersede("approval/svc-fake-a", digest_of(GEN1), GEN3),
           note="A stale digest is how a superseded decision gets quietly reinstated.")
    t.deny("superseding a slot that was never created",
           {"slot": "approval/svc-never-seen", "predecessor": digest_of(GEN1)[:20] + "..."},
           lambda: slots.supersede("approval/svc-never-seen", digest_of(GEN1), GEN2))
    t.deny("creating a slot key that already exists",
           {"slot": "approval/svc-fake-a", "exists since": "the first create"},
           lambda: slots.create("approval/svc-fake-a", GEN3),
           evidence=lambda: f"slot still holds generation "
                            f"{slots.get('approval/svc-fake-a').value['generation']}",
           note="Create is not an alias for overwrite.")
    return t


if __name__ == "__main__":
    main(build, __file__)

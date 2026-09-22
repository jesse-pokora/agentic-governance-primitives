"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from review_loop import BoundedReviewEpoch  # noqa: E402


def build() -> Trace:
    epoch = BoundedReviewEpoch()
    t = Trace(
        app="bounded-review-epoch-escalation",
        claim=(
            "After 3 review rounds with open findings, the loop stops and requires a new, "
            "hash-bound human reauthorization naming the exact terminal evidence — it "
            "cannot self-extend."
        ),
        enforcement="deterministic",
        denial_type="EscalationRequired / ReauthorizationDenied",
    )
    findings = ["F-001", "F-002"]
    for n in (1, 2, 3):
        t.allow(f"review round {n} of 3, findings still open",
                {"round": n, "open findings": ", ".join(findings)},
                lambda: epoch.submit_round(list(findings)),
                evidence=lambda: f"rounds completed: {epoch.rounds_completed}")

    t.deny("round 4 — the loop has reached its cap",
           {"round": 4, "open findings": ", ".join(findings), "cap": 3},
           lambda: epoch.submit_round(list(findings)),
           evidence=lambda: f"rounds completed: {epoch.rounds_completed}",
           note="A loop that could grant itself another round is not capped.")

    t.deny("reauthorizing with the wrong evidence hash",
           {"provided": "0000...0000", "required": "hash of the exact terminal evidence"},
           lambda: epoch.reauthorize("0" * 64),
           note="Reauthorization names what is being reauthorized, or it is just a "
                "button that says continue.")
    return t


if __name__ == "__main__":
    main(build, __file__)

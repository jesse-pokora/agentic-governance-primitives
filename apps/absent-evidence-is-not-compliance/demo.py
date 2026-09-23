"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from observation import RunLedger, merge  # noqa: E402

DECLARED = ("RS-001", "RS-002", "RS-003")


def build() -> Trace:
    partial = RunLedger(declared=DECLARED)
    partial.record("RS-001", "passed", "fixture accepted by the detector")

    t = Trace(
        app="absent-evidence-is-not-compliance",
        claim=(
            "A criterion whose checker exists but produced no evidence in this run is "
            "recorded as not_observed — never as passed, and never dropped from the "
            "report."
        ),
        enforcement="deterministic",
        denial_type="ObservationRejected",
    )
    t.allow(
        "a run that exercised one of three declared criteria",
        {"declared": ", ".join(DECLARED), "observed": "RS-001"},
        lambda: [f"{r.criterion_id}: {r.status}" for r in partial.report()],
        evidence=lambda: f"observed {partial.observed()[0]} of {partial.observed()[1]}; "
                         f"clean={partial.clean()}",
        note="Nothing failed, and the run is not clean. Those are different "
             "statements, and only one of them is usually true.",
    )
    complete = RunLedger(declared=DECLARED)
    for criterion in DECLARED:
        complete.record(criterion, "passed", "fixture accepted by the detector")
    t.allow(
        "a run that exercised all three",
        {"declared": ", ".join(DECLARED), "observed": "all"},
        lambda: f"clean={complete.clean()}, observed={complete.observed()}",
    )
    t.deny(
        "recording a pass with no evidence behind it",
        {"criterion": "RS-002", "status": "passed", "evidence": "(blank)"},
        lambda: RunLedger(declared=DECLARED).record("RS-002", "passed", "   "),
        note="An assertion with nothing behind it is indistinguishable from not "
             "looking, right up until somebody asks what the evidence was.",
    )
    t.deny(
        "marking a criterion not_observed on purpose",
        {"criterion": "RS-002", "status": "not_observed"},
        lambda: RunLedger(declared=DECLARED).record("RS-002", "not_observed", "skipped"),
        note="It is the absence of a record, not a record. Writing it deliberately "
             "would be worse than the gap it describes.",
    )
    t.deny(
        "observing a criterion nobody declared",
        {"criterion": "RS-999", "declared": ", ".join(DECLARED)},
        lambda: RunLedger(declared=DECLARED).record("RS-999", "passed", "evidence"),
    )

    first, second = RunLedger(declared=DECLARED), RunLedger(declared=DECLARED)
    first.record("RS-001", "passed", "run 1")
    second.record("RS-002", "passed", "run 2")
    t.allow(
        "two partial runs merged",
        {"run 1": "RS-001", "run 2": "RS-002"},
        lambda: f"observed={merge(first, second).observed()}, "
                f"clean={merge(first, second).clean()}",
        evidence=lambda: "coverage accumulates; RS-003 is still unobserved",
    )
    disagreeing = RunLedger(declared=DECLARED)
    disagreeing.record("RS-001", "failed", "run 3")
    t.deny(
        "two runs that disagree about the same criterion",
        {"run 1": "RS-001 passed", "run 3": "RS-001 failed"},
        lambda: merge(first, disagreeing),
        note="Refused rather than resolved. Picking a winner silently is how a flaky "
             "failure becomes a pass.",
    )
    return t


if __name__ == "__main__":
    main(build, __file__)

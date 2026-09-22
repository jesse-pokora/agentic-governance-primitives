"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from validation import STAGES, classify  # noqa: E402

FIXTURES = [
    ("a record with no id", {"amount": 10}),
    ("an amount of the wrong type", {"id": "toy-1", "amount": "ten"}),
    ("an amount out of range", {"id": "toy-2", "amount": -5}),
    ("a valid record", {"id": "toy-3", "amount": 10}),
]


def build() -> Trace:
    t = Trace(
        app="non-overlapping-error-mapping",
        claim=(
            "Every test fixture reaches exactly one named validation stage and exactly "
            "one named error — never two, never zero."
        ),
        enforcement="deterministic",
        denial_type="n/a — this app returns a classified Outcome",
    )
    for label, fixture in FIXTURES:
        t.verdict(label, dict(fixture, stages=" -> ".join(s.name for s in STAGES)),
                  lambda f=fixture: classify(f),
                  lambda out: out.error is None,
                  lambda out: (f"stage={out.stage}" if out.error is None
                               else f"stage={out.stage} error={out.error}"),
                  evidence=lambda: "exactly one stage, exactly one error")
    t.verdict("every fixture lands on exactly one stage — never two, never zero",
              {"fixtures": len(FIXTURES), "stages": len(STAGES)},
              lambda: [classify(f).stage for _, f in FIXTURES],
              lambda stages: len(set(stages)) == len(stages),
              lambda stages: f"{len(set(stages))} distinct stages for {len(stages)} fixtures",
              note="Overlapping stages are how a validation suite passes while the "
                   "error a user sees is arbitrary.")
    return t


if __name__ == "__main__":
    main(build, __file__)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from review_agent import review  # noqa: E402

RISKY = "def run(expr):\n    return eval(expr)\n"
CLEAN = "def add(a, b):\n    return a + b\n"


def build() -> Trace:
    t = Trace(
        app="single-purpose-adversarial-reviewer",
        claim=(
            "One adversarial-review agent, schema-in/findings-out, callable with zero "
            "pipeline, zero orchestrator, and no state carried between calls."
        ),
        enforcement="hybrid",
        denial_type="InvalidReviewPayload",
    )
    t.allow("content containing an eval call",
            {"artifact_id": "toy-1", "content": RISKY.replace("\n", " / ")},
            lambda: review({"artifact_id": "toy-1", "content": RISKY}),
            evidence=lambda: "one call, no orchestrator, no prior state")
    t.allow("content with nothing to flag",
            {"artifact_id": "toy-2", "content": CLEAN.replace("\n", " / ")},
            lambda: review({"artifact_id": "toy-2", "content": CLEAN}),
            evidence=lambda: "findings is empty, and the output shape is unchanged",
            note="A reviewer that only ever returns findings is a reviewer nobody "
                 "can calibrate.")
    t.allow("the same input reviewed twice",
            {"artifact_id": "toy-1", "calls": 2},
            lambda: "identical" if review({"artifact_id": "toy-1", "content": RISKY})
                    == review({"artifact_id": "toy-1", "content": RISKY}) else "differed",
            evidence=lambda: "pure: no state is carried between calls")
    t.deny("an input missing a required field",
           {"payload": '{"content": "..."}', "missing": "artifact_id"},
           lambda: review({"content": RISKY}),
           note="Schema in, schema out. The envelope is deterministic even where the "
                "content is not.")
    t.deny("an input carrying a field outside the schema",
           {"payload": '{"artifact_id": ..., "content": ..., "priority": "high"}',
            "unexpected": "priority"},
           lambda: review({"artifact_id": "toy-1", "content": RISKY, "priority": "high"}),
           note="Extra fields are how a single-purpose agent quietly grows a second "
                "purpose.")
    return t


if __name__ == "__main__":
    main(build, __file__)

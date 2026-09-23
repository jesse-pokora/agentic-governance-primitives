"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from attribution import Run, attribute  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

FACTORS = {"task": "summarize-toy-repo", "model": "toy-model-v2", "corpus": "toy-corpus"}
BOTH = {"INS-001", "INS-002"}
FACTOR_TEXT = "task=summarize-toy-repo, model=toy-model-v2, corpus=toy-corpus"


def run(id, instructions, outcome, **overrides):
    return Run.of(id, instructions, dict(FACTORS, **overrides), outcome)


def build() -> Trace:
    t = Trace(
        app="ablation-required-for-causal-claim",
        claim=(
            "A finding may be recorded as caused by an instruction only when a "
            "leave-one-out comparison exists — two runs identical in every declared "
            "factor except that instruction. Without one it is recorded as a "
            "correlation."
        ),
        enforcement="deterministic",
        denial_type="AttributionRefused",
    )
    t.allow("a violated instruction alongside a poor outcome, with no control run",
            {"run": "r1", "instructions": "INS-001, INS-002", "outcome": "poor",
             "control": "(none)"},
            lambda: attribute("INS-001", run("r1", BOTH, "poor")).relation,
            evidence=lambda: "recorded, not discarded — an observed omission is worth "
                             "knowing, it just is not a cause",
            note="The conclusion everybody reaches and almost nobody tests. On the "
                 "strength of this coincidence an instruction earns permanent "
                 "residency in a prompt that every future run pays for.")
    t.allow("a clean leave-one-out comparison",
            {"treatment": "r1 with INS-001, outcome good",
             "control": "r2 without INS-001, outcome poor", "factors": FACTOR_TEXT},
            lambda: attribute("INS-001", run("r1", BOTH, "good"),
                              run("r2", {"INS-002"}, "poor")).relation,
            evidence=lambda: "identical in every declared factor except the instruction")
    t.allow("the same outcome with and without it",
            {"treatment": "r1 with INS-001, outcome good",
             "control": "r2 without INS-001, outcome good"},
            lambda: attribute("INS-001", run("r1", BOTH, "good"),
                              run("r2", {"INS-002"}, "good")).relation,
            evidence=lambda: "the result that retires an instruction",
            note="Nobody goes looking for this one, which is why prompts only ever "
                 "grow.")
    t.deny("the control run also changed the model",
           {"treatment": "model=toy-model-v2", "control": "model=toy-model-v3"},
           lambda: attribute("INS-001", run("r1", BOTH, "good"),
                             run("r2", {"INS-002"}, "poor", model="toy-model-v3")),
           evidence=lambda: "the denial names the confound",
           note="With two differences the comparison cannot say which did the work.")
    t.deny("the control dropped two instructions at once",
           {"treatment": "INS-001, INS-002", "control": "(none)"},
           lambda: attribute("INS-001", run("r1", BOTH, "good"), run("r2", set(), "poor")))
    t.deny("the control still has the instruction in effect",
           {"treatment": "INS-001, INS-002", "control": "INS-001, INS-002"},
           lambda: attribute("INS-001", run("r1", BOTH, "good"), run("r2", BOTH, "poor")),
           note="Not an ablation at all.")
    return t


if __name__ == "__main__":
    main(build, __file__)

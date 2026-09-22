"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from objectives import Action, Run  # noqa: E402

DECLARED = {"summarize-repository", "record-evidence"}
DECLARED_TEXT = "summarize-repository, record-evidence"


class Spy:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return "action performed"


def build() -> Trace:
    source = set(DECLARED)
    run = Run.declaring(source)
    spy = Spy()

    t = Trace(
        app="declared-objective-conformance",
        claim=(
            "Every action must cite an objective declared for the run — an action citing "
            "nothing, or citing an objective never declared, is refused before it "
            "executes, and the declared set cannot be widened from inside the run."
        ),
        enforcement="deterministic",
        denial_type="ObjectiveViolation",
    )
    t.allow(
        "an action citing a declared objective",
        {"action": "read_repo", "serves": "summarize-repository",
         "declared": DECLARED_TEXT},
        lambda: run.perform(Action("read_repo", ("summarize-repository",)), spy),
        evidence=lambda: f"action bodies entered: {spy.calls}",
    )
    t.deny(
        "an action citing nothing at all",
        {"action": "open_pull_request", "serves": "(nothing)"},
        lambda: run.perform(Action("open_pull_request", ()), spy),
        evidence=lambda: f"action bodies entered: {spy.calls} — unchanged",
        note="An agent does not go off-mission by announcing it. It takes one "
             "reasonable-looking action nobody asked for.",
    )
    t.deny(
        "an action serving a goal nobody declared",
        {"action": "deploy", "serves": "improve-deployment-speed",
         "declared": DECLARED_TEXT},
        lambda: run.perform(Action("deploy", ("improve-deployment-speed",)), spy),
        evidence=lambda: f"action bodies entered: {spy.calls}",
    )
    t.deny(
        "one undeclared objective alongside a valid one",
        {"action": "deploy", "serves": "summarize-repository, ship-it"},
        lambda: run.perform(Action("deploy", ("summarize-repository", "ship-it")), spy),
        note="The valid half does not rescue it. The unauthorized part would happen "
             "anyway.",
    )
    t.deny(
        "an action that has drifted twice",
        {"action": "drift", "serves": "alpha, beta", "declared": DECLARED_TEXT},
        lambda: run.perform(Action("drift", ("alpha", "beta")), spy),
        evidence=lambda: "every undeclared objective is named, not just the first",
    )
    source.add("deploy-to-production")
    t.deny(
        "widening the objective set from outside, then citing it",
        {"declared at start": DECLARED_TEXT,
         "added afterwards": "deploy-to-production"},
        lambda: run.perform(Action("deploy", ("deploy-to-production",)), spy),
        note="The declaration is frozen at the start. A run that can widen its own "
             "remit has no remit.",
    )
    t.allow(
        "an action serving two declared objectives at once",
        {"action": "write_evidence", "serves": DECLARED_TEXT},
        lambda: run.perform(
            Action("write_evidence", ("summarize-repository", "record-evidence")), spy
        ),
        evidence=lambda: f"objectives actually served: "
                         f"{sorted(run.objectives_served())}",
    )
    return t


if __name__ == "__main__":
    main(build, __file__)

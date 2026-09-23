"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from policy_gate import Instruction, evaluate  # noqa: E402

ARTIFACT = "class Service:\n    def __init__(self, repo):\n        self.repo = repo\n"


def always(verdict, detail=""):
    return lambda artifact: (verdict, detail)


POLICY = [
    Instruction("INS-001", "Constructors receive their collaborators",
                "AGENTS.md:12-14", always("passed", "Service takes repo as a parameter")),
    Instruction("INS-002", "No module-level singletons", "AGENTS.md:16",
                always("not_applicable", "no module-level assignments in this artifact")),
    Instruction("INS-003", "Write clearly and for the reader", "AGENTS.md:20"),
]


def build() -> Trace:
    t = Trace(
        app="instruction-policy-gate",
        claim=(
            "Every declared instruction receives an explicit verdict from a fixed "
            "vocabulary — and an instruction with no mechanical checker is reported as "
            "unenforceable, never counted as satisfied."
        ),
        enforcement="deterministic",
        denial_type="PolicyRejected",
    )
    report = evaluate(POLICY, ARTIFACT)

    t.allow(
        "three instructions, two with checkers",
        {"INS-001": "has a checker", "INS-002": "has a checker",
         "INS-003": "prose, no mechanical check"},
        lambda: [f"{v.instruction_id}: {v.verdict}" for v in report.verdicts],
        evidence=lambda: f"one row per declared instruction: {len(report.verdicts)} of "
                         f"{len(POLICY)}",
        note="The instructions nobody could check are exactly the ones worth knowing "
             "about. Leaving them out of the report is how a policy that verifies a "
             "third of itself reads as green.",
    )
    t.allow(
        "what the report says about coverage",
        {"admitted": "nothing failed", "question": "was everything checked?"},
        lambda: f"admitted={report.admitted}, coverage={report.coverage()[0]} of "
                f"{report.coverage()[1]} checked",
        evidence=lambda: "'nothing failed' and 'everything was verified' are different "
                         "statements",
    )
    t.allow(
        "not_applicable is not passed",
        {"INS-002": "no module-level assignments exist to check"},
        lambda: [v.instruction_id for v in report.of("not_applicable")],
        note="An instruction with nothing to apply to has not been satisfied. "
             "Collapsing the two inflates every percentage in the report.",
    )
    failing = list(POLICY) + [
        Instruction("INS-004", "No direct construction of collaborators",
                    "AGENTS.md:22", always("failed", "Repo() built at line 7"))
    ]
    blocked = evaluate(failing, ARTIFACT)
    t.allow(
        "one instruction fails",
        {"INS-004": "checker reports a violation"},
        lambda: f"admitted={blocked.admitted}, failed="
                f"{[v.instruction_id for v in blocked.failures]}",
        evidence=lambda: blocked.failures[0].detail,
    )
    t.deny(
        "a checker trying to mark its own instruction unenforceable",
        {"INS-009": "checker returns 'unenforceable'"},
        lambda: evaluate([Instruction("INS-009", "t", "s", always("unenforceable"))],
                         ARTIFACT),
        note="Unenforceable is what the absence of a checker produces. If a checker "
             "could return it, an instruction could mark itself unverifiable and "
             "vanish from the part of the report anyone reads.",
    )
    t.deny(
        "a checker that invents a verdict",
        {"INS-005": "checker returns 'probably fine'"},
        lambda: evaluate([Instruction("INS-005", "t", "s", always("probably fine"))],
                         ARTIFACT),
    )
    t.deny(
        "a checker that raises",
        {"INS-006": "checker raises RuntimeError"},
        lambda: evaluate([Instruction("INS-006", "t", "s",
                                      lambda a: (_ for _ in ()).throw(RuntimeError("bug")))],
                         ARTIFACT),
        note="A broken checker invalidates the whole report rather than failing one "
             "instruction. A report that is wrong somewhere unknown is worse than no "
             "report.",
    )
    return t


if __name__ == "__main__":
    main(build, __file__)

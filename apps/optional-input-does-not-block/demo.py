"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from startup import InputSpec, evaluate_startup  # noqa: E402

SPECS = [InputSpec("prompt", True), InputSpec("run_id", False),
         InputSpec("head_commit", False), InputSpec("evidence_packet", False),
         InputSpec("approval_record", False)]
DECLARED = "required: prompt | optional: run_id, head_commit, evidence_packet, approval_record"


def build() -> Trace:
    t = Trace(
        app="optional-input-does-not-block",
        claim=(
            "A run starts when every required input is present, even if every optional "
            "one is missing — a missing optional input is recorded and the run marked "
            "degraded, never escalated into a stop."
        ),
        enforcement="deterministic",
        denial_type="StartupRefused",
    )
    t.allow("a bare prompt, with every optional input absent",
            {"supplied": "prompt only", "spec": DECLARED},
            lambda: evaluate_startup(SPECS, {"prompt": "summarize the toy repository"}).missing_optional,
            evidence=lambda: "started, degraded, and the missing inputs are recorded",
            note="This is the case the rest of this catalog would be tempted to refuse. "
                 "An agent that cannot start without context it never needed is "
                 "governed and useless.")
    t.allow("a full envelope",
            {"supplied": "prompt, run_id, head_commit, evidence_packet, approval_record"},
            lambda: evaluate_startup(SPECS, {
                "prompt": "toy", "run_id": "r-1", "head_commit": "a" * 40,
                "evidence_packet": {"k": 1}, "approval_record": {"by": "toy-human"}}).degraded,
            evidence=lambda: "degraded=False — nothing missing")
    t.allow("a field nobody declared",
            {"supplied": "prompt, workspace_hint", "spec": DECLARED},
            lambda: evaluate_startup(SPECS, {"prompt": "toy", "workspace_hint": "/toy"}).extra_context,
            evidence=lambda: "carried as context, not refused",
            note="Strictness belongs where extra data would otherwise be acted on. At "
                 "intake nobody reads it; in a closed output schema it might be an "
                 "instruction the caller expects honoured.")
    t.deny("the one required input is missing",
           {"supplied": "run_id only", "required": "prompt"},
           lambda: evaluate_startup(SPECS, {"run_id": "r-1"}),
           note="Fail-closed still applies — to required inputs.")
    t.deny("two required inputs missing, both named at once",
           {"supplied": "nothing", "required": "prompt, target"},
           lambda: evaluate_startup(SPECS + [InputSpec("target", True)], {}),
           evidence=lambda: "every missing required input in one round",
           note="The other apps here report the first violation. This one is answering "
                "'what do you need from me', so it reports the whole list.")
    t.deny("a required input supplied as an empty string",
           {"supplied": 'prompt=""'},
           lambda: evaluate_startup(SPECS, {"prompt": ""}),
           note="Present-but-empty is missing wearing a costume.")
    return t


if __name__ == "__main__":
    main(build, __file__)

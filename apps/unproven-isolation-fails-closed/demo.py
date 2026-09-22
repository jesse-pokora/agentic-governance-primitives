"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from isolation import (  # noqa: E402
    Assertion, CapabilityDeclaration, Probe, evaluate_isolation,
)

PASSING = [Probe("network_blocked", True), Probe("filesystem_readonly", True)]
ASSERTED = [Assertion("--external-sandbox", "operator claim")]
DECLARED = [CapabilityDeclaration(denies_write=True, denies_terminal=True)]


def build() -> Trace:
    t = Trace(
        app="unproven-isolation-fails-closed",
        claim=(
            "A run proceeds only when isolation is verified by a probe that actually ran "
            "— an operator assertion and a child's capability declaration are recorded "
            "for audit and contribute nothing to the verdict."
        ),
        enforcement="deterministic",
        denial_type="IsolationUnproven",
    )
    t.allow("two probes ran and both passed",
            {"probes": "network_blocked=pass, filesystem_readonly=pass", "assertions": "none"},
            lambda: evaluate_isolation(PASSING).verified,
            evidence=lambda: "the verdict is a function of probe results only")
    t.deny("the operator asserts a sandbox is in place",
           {"probes": "none", "assertion": "--external-sandbox (operator claim)"},
           lambda: evaluate_isolation([], assertions=ASSERTED),
           evidence=lambda: "the denial names what was offered instead of evidence",
           note="A claim about the world and a measurement of the world are different "
                "objects. Storing them in the same field loses the argument.")
    t.deny("the child advertises that it denies writes and terminals",
           {"probes": "none", "declaration": "denies_write=True, denies_terminal=True"},
           lambda: evaluate_isolation([], declarations=DECLARED),
           note="The child is describing its own protocol, not the operating system it "
                "runs on. An honest child tells the truth about something that does "
                "not constrain a dishonest one.")
    t.deny("an assertion cannot rescue a probe that failed",
           {"probes": "network_blocked=FAIL", "assertion": "--external-sandbox"},
           lambda: evaluate_isolation([Probe("network_blocked", False)], assertions=ASSERTED))
    t.allow("assertions are still carried into the record",
            {"probes": "both pass", "assertion": "--external-sandbox", "declaration": "yes"},
            lambda: evaluate_isolation(PASSING, ASSERTED, DECLARED).assertions[0].claimed_by,
            evidence=lambda: "recorded for audit, counted for nothing")
    t.deny("the local-development bypass flag, passed on its own",
           {"allow_unisolated": True, "proof": "none"},
           lambda: evaluate_isolation([], allow_unisolated=True),
           note="A flag that works because it was passed is a flag that works in "
                "production.")
    t.allow("the bypass with a proof that actually returns True",
            {"allow_unisolated": True, "proof": "returns True"},
            lambda: f"allowed, verified={evaluate_isolation([], allow_unisolated=True, local_development_proof=lambda: True).verified}",
            evidence=lambda: "allowed and honestly labelled unverified",
            note="The audit trail is the one artifact that has to survive the "
                 "convenience.")
    return t


if __name__ == "__main__":
    main(build, __file__)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from escalation_gate import Tier, TieredEscalationGate  # noqa: E402

GOOD = {"text": "svc-fake-a is owned by toy-team-alpha", "source_key": "svc-fake-a.owner"}
UNGROUNDED = {"text": "svc-fake-a is probably fine", "source_key": None}


class SpyTier:
    def __init__(self, result, raises=False):
        self.calls, self.result, self.raises = 0, result, raises

    def __call__(self, prompt):
        self.calls += 1
        if self.raises:
            raise RuntimeError("toy tier failure")
        return self.result


def grounded(output):
    return isinstance(output, dict) and bool(output.get("source_key"))


def build() -> Trace:
    t = Trace(
        app="tiered-model-escalation-gate",
        claim=(
            "A cheap tier's output is used only if it passes the declared deterministic "
            "check — otherwise the call escalates to the next tier, and the ledger "
            "records which tier actually answered."
        ),
        enforcement="hybrid",
        denial_type="NoTierPassed",
    )
    cheap, strong = SpyTier(GOOD), SpyTier(GOOD)
    gate = TieredEscalationGate([Tier("cheap", cheap), Tier("strong", strong)], grounded)
    t.allow("the cheap tier returns output that passes the check",
            {"tiers": "cheap, strong", "check": "output cites a source_key"},
            lambda: gate.answer("toy prompt").answered_by,
            evidence=lambda: f"cheap called {cheap.calls}x, strong called {strong.calls}x")

    cheap2, strong2 = SpyTier(UNGROUNDED), SpyTier(GOOD)
    gate2 = TieredEscalationGate([Tier("cheap", cheap2), Tier("strong", strong2)], grounded)
    t.allow("the cheap tier fails the check, so the call escalates",
            {"cheap returns": "no source_key", "check": "output cites a source_key"},
            lambda: gate2.answer("toy prompt").answered_by,
            evidence=lambda: f"cheap called {cheap2.calls}x, strong called {strong2.calls}x; "
                             f"ledger records answered_by=strong")

    cheap3, strong3 = SpyTier(None, raises=True), SpyTier(GOOD)
    gate3 = TieredEscalationGate([Tier("cheap", cheap3), Tier("strong", strong3)], grounded)
    t.allow("the cheap tier raises, and the call escalates past it",
            {"cheap": "raises RuntimeError", "strong": "returns grounded output"},
            lambda: gate3.answer("toy prompt").answered_by,
            note="A cheap tier having a bad day should cost latency, not availability.")

    only_strong = SpyTier(UNGROUNDED)
    gate4 = TieredEscalationGate([Tier("strong", only_strong)], grounded)
    t.deny("the expensive tier's output fails the same check",
           {"tier": "strong", "returns": "no source_key"},
           lambda: gate4.answer("toy prompt"),
           evidence=lambda: f"ledger entries: {len(gate4.ledger)} — nothing accepted",
           note="Cost does not buy trust. There is no degraded mode that returns the "
                "least bad failing output.")
    return t


if __name__ == "__main__":
    main(build, __file__)

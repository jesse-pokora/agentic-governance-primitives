"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from budget import BoundedExecutionBudget, Charge  # noqa: E402
from demo_trace import Trace, main  # noqa: E402


class SpyAction:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return "toy-action-result"


def build() -> Trace:
    budget = BoundedExecutionBudget({"tool_calls": 3, "cost_units": 100})
    action = SpyAction()

    t = Trace(
        app="bounded-execution-budget",
        claim=(
            "A run halts at the first action that would exceed a declared budget — the "
            "over-budget action never executes, nothing is partially charged, and the "
            "budget cannot be extended from inside the run."
        ),
        enforcement="deterministic",
        denial_type="BudgetDenied",
    )
    for n in (1, 2, 3):
        t.allow(f"tool call {n} of a 3-call budget",
                {"resource": "tool_calls", "amount": 1,
                 "remaining_before": budget.remaining("tool_calls")},
                lambda: budget.run(Charge("tool_calls", 1), action),
                evidence=lambda: f"actions executed: {action.calls}")

    t.deny("the fourth call would cross the cap",
           {"resource": "tool_calls", "amount": 1, "limit": 3, "spent": 3},
           lambda: budget.run(Charge("tool_calls", 1), action),
           evidence=lambda: f"actions executed: {action.calls} — unchanged",
           note="Checked before charging, charged before running.")

    t.deny("an affordable charge against a different resource, after the halt",
           {"resource": "cost_units", "amount": 5, "remaining": 100},
           lambda: budget.run(Charge("cost_units", 5), action),
           evidence=lambda: f"actions executed: {action.calls}",
           note="A meter that keeps serving whatever still fits lets a run route "
                "around its own cap.")

    fresh = BoundedExecutionBudget({"tool_calls": 3})
    t.deny("a resource nobody declared",
           {"resource": "gpu_seconds", "amount": 1, "declared": "tool_calls only"},
           lambda: fresh.run(Charge("gpu_seconds", 1), action),
           note="Undeclared is refused, never free.")
    return t


if __name__ == "__main__":
    main(build, __file__)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from approval_gate import approve_and_execute, plan_hash, show_plan  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

PLAN = "DROP TABLE toy_customers;\nDELETE FROM toy_orders WHERE 1=1;"
ALTERED = PLAN + "\nDROP TABLE toy_audit_log;"


def build() -> Trace:
    shown = show_plan(PLAN)
    t = Trace(
        app="exact-plan-approval-gate",
        claim=(
            "A destructive action can only be approved by echoing back the exact SHA-256 "
            "of the plan that was shown — a \"yes\" with no hash is rejected."
        ),
        enforcement="deterministic",
        denial_type="ApprovalDenied",
    )
    t.allow("the operator echoes the exact hash of the plan shown",
            {"plan": PLAN.splitlines()[0] + " ...", "provided": shown.plan_hash[:24] + "..."},
            lambda: approve_and_execute(PLAN, shown.plan_hash),
            evidence=lambda: "provided value equals the shown plan's SHA-256")
    t.deny('a bare "yes" carries no evidence of what was approved',
           {"plan": PLAN.splitlines()[0] + " ...", "provided": "yes"},
           lambda: approve_and_execute(PLAN, "yes"),
           note="Consent has to name what was consented to.")
    t.deny("the plan changed after it was shown",
           {"plan": "...plus DROP TABLE toy_audit_log;", "provided": shown.plan_hash[:24] + "..."},
           lambda: approve_and_execute(ALTERED, shown.plan_hash),
           evidence=lambda: f"hash now {plan_hash(ALTERED)[:16]}..., approval names "
                            f"{shown.plan_hash[:16]}...",
           note="The approval is bound to bytes, so an edit after approval invalidates it.")
    return t


if __name__ == "__main__":
    main(build, __file__)

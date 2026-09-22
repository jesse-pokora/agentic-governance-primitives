"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from token_account import TokenAccount, Usage, ZERO_USAGE  # noqa: E402


def build() -> Trace:
    account = TokenAccount()
    t = Trace(
        app="measured-token-accounting",
        claim=(
            "An unmeasured model call is refused rather than counted as zero, and the "
            "recorded per-call parts must reconcile exactly with the provider's own "
            "reported total."
        ),
        enforcement="deterministic",
        denial_type="AccountingRejected",
    )
    t.allow("a call whose usage the provider reported",
            {"call_id": "call-1", "prompt_tokens": 100, "completion_tokens": 20},
            lambda: account.record("call-1", Usage(100, 20)) or "recorded",
            evidence=lambda: f"running total: {account.total().total_tokens} tokens")
    t.allow("a call that genuinely consumed nothing",
            {"call_id": "call-2", "prompt_tokens": 0, "completion_tokens": 0},
            lambda: account.record("call-2", ZERO_USAGE) or "recorded",
            evidence=lambda: f"calls recorded: {account.call_count}",
            note="Zero is a measurement. It is recorded, and it is not the same thing "
                 "as the next step.")
    t.deny("a call whose usage never arrived",
           {"call_id": "call-3", "usage": "None — provider reported nothing"},
           lambda: account.record("call-3", None),
           evidence=lambda: f"calls recorded: {account.call_count} — unchanged",
           note="Treating unknown as zero is how a budget drifts away from reality "
                "while every number in it stays defensible.")
    t.deny("the same call recorded twice",
           {"call_id": "call-1", "prompt_tokens": 100, "completion_tokens": 20},
           lambda: account.record("call-1", Usage(100, 20)),
           evidence=lambda: f"running total: {account.total().total_tokens} tokens",
           note="The other direction a total can drift.")
    t.deny("the provider bills for a call this account never saw",
           {"measured here": "120 tokens", "provider reports": "180 tokens"},
           lambda: account.reconcile(Usage(150, 30)),
           evidence=lambda: "sum of the parts must equal the whole",
           note="A single running counter cannot detect this. A per-call ledger can.")
    return t


if __name__ == "__main__":
    main(build, __file__)

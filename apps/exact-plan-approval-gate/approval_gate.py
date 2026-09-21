"""Exact-plan approval gate.

A toy gate for destructive actions: the only valid approval is the exact
SHA-256 hex digest of the plan text that was shown to the human. A plain
"yes" — or the hash of a plan that has since changed — is rejected.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


def plan_hash(plan_text: str) -> str:
    return hashlib.sha256(plan_text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ShownPlan:
    """What gets displayed to the human before they approve."""

    plan_text: str
    plan_hash: str


class ApprovalDenied(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def show_plan(plan_text: str) -> ShownPlan:
    return ShownPlan(plan_text=plan_text, plan_hash=plan_hash(plan_text))


def approve_and_execute(current_plan_text: str, provided_value: str) -> str:
    """Execute the plan only if provided_value is the exact hash of the
    *current* plan text.

    Raises ApprovalDenied for anything else, including a bare "yes", a wrong
    hash, or the hash of a plan that has since been edited.
    """
    expected = plan_hash(current_plan_text)
    if provided_value != expected:
        raise ApprovalDenied(
            f"approval_rejected: provided value does not match the exact "
            f"SHA-256 of the current plan (expected={expected})"
        )
    return f"executed: {current_plan_text}"

"""Tiered model escalation gate.

A cheap tier's output is used only if it passes a declared deterministic
check. If it fails, the call escalates to the next tier, and the ledger
records which tier actually answered.

The point is not that cheap models are bad — it is that "we asked the cheap
one first" must never be a reason output reaches a caller unchecked. Every
tier faces the same gate, so cost and trust stay independent: a tier earns
acceptance by passing, not by being expensive.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class NoTierPassed(Exception):
    def __init__(self, attempts: list["Attempt"]):
        super().__init__(
            "no_tier_passed: " + ", ".join(a.tier for a in attempts)
        )
        self.reason = "no_tier_passed"
        self.attempts = attempts


@dataclass(frozen=True)
class Tier:
    name: str
    call: Callable[[str], Any]


@dataclass(frozen=True)
class Attempt:
    tier: str
    passed: bool


@dataclass(frozen=True)
class Answer:
    value: Any
    answered_by: str
    attempts: tuple[Attempt, ...]


class TieredEscalationGate:
    """Try tiers in declared order; return only output that passed the check."""

    def __init__(self, tiers: list[Tier], check: Callable[[Any], bool]):
        if not tiers:
            raise ValueError("at least one tier is required")
        self._tiers = tuple(tiers)
        self._check = check
        self._ledger: list[Answer] = []

    @property
    def ledger(self) -> list[Answer]:
        return self._ledger

    def answer(self, prompt: str) -> Answer:
        """Return the first tier's output that passes the check.

        A tier that raises is recorded as a failed attempt and escalated past —
        a broken cheap tier must not take the whole call down with it. A tier
        whose output fails the check is never returned, so there is no path by
        which unchecked output reaches the caller.
        """
        attempts: list[Attempt] = []

        for tier in self._tiers:
            try:
                candidate = tier.call(prompt)
                passed = bool(self._check(candidate))
            except Exception:
                attempts.append(Attempt(tier=tier.name, passed=False))
                continue

            attempts.append(Attempt(tier=tier.name, passed=passed))
            if passed:
                answer = Answer(
                    value=candidate,
                    answered_by=tier.name,
                    attempts=tuple(attempts),
                )
                self._ledger.append(answer)
                return answer

        raise NoTierPassed(attempts)

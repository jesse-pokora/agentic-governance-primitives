"""Bounded review-epoch escalation.

A review loop that hard-caps at N rounds. If findings are still open at the
cap, the loop stops and requires a *new*, hash-bound human reauthorization
naming the exact terminal evidence before another round can run. It cannot
self-extend: no code path advances past the cap without that reauthorization.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class EscalationRequired(Exception):
    def __init__(self, terminal_evidence_hash: str):
        super().__init__(
            f"escalation_required: reauthorize with hash {terminal_evidence_hash}"
        )
        self.terminal_evidence_hash = terminal_evidence_hash


class ReauthorizationDenied(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass
class RoundResult:
    round_number: int
    status: str  # "closed" | "continue" | "escalation_required"
    terminal_evidence_hash: str | None = None


class BoundedReviewEpoch:
    def __init__(self, max_rounds_per_epoch: int = 3):
        self._max_rounds_per_epoch = max_rounds_per_epoch
        self._rounds: list[list[str]] = []
        self._awaiting_reauthorization = False
        self._terminal_evidence_hash: str | None = None
        self._rounds_since_last_reauthorization = 0

    @property
    def rounds_completed(self) -> int:
        return len(self._rounds)

    def submit_round(self, open_findings: list[str]) -> RoundResult:
        if self._awaiting_reauthorization:
            raise EscalationRequired(self._terminal_evidence_hash)

        round_number = len(self._rounds) + 1
        self._rounds.append(list(open_findings))
        self._rounds_since_last_reauthorization += 1

        if not open_findings:
            return RoundResult(round_number=round_number, status="closed")

        if self._rounds_since_last_reauthorization >= self._max_rounds_per_epoch:
            evidence = {
                "round": round_number,
                "open_findings": list(open_findings),
            }
            evidence_hash = hashlib.sha256(
                canonical_json(evidence).encode("utf-8")
            ).hexdigest()
            self._awaiting_reauthorization = True
            self._terminal_evidence_hash = evidence_hash
            return RoundResult(
                round_number=round_number,
                status="escalation_required",
                terminal_evidence_hash=evidence_hash,
            )

        return RoundResult(round_number=round_number, status="continue")

    def reauthorize(self, evidence_hash: str) -> None:
        """A human names the exact terminal evidence hash to unlock exactly
        one further epoch of up to max_rounds_per_epoch rounds.

        The system itself never calls this — only an explicit external
        caller with the exact hash can clear the escalation.
        """
        if not self._awaiting_reauthorization:
            raise ReauthorizationDenied("not_awaiting_reauthorization")

        if evidence_hash != self._terminal_evidence_hash:
            raise ReauthorizationDenied("evidence_hash_mismatch")

        self._awaiting_reauthorization = False
        self._terminal_evidence_hash = None
        self._rounds_since_last_reauthorization = 0

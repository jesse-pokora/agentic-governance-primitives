"""Absent evidence is not compliance.

A criterion whose checker exists but produced no evidence in this run is
recorded as `not_observed`. It is never recorded as passed, and it is never
dropped from the report.

This is a different failure from having no checker at all. There the policy is
incomplete; here the policy is fine and the *run* is. Both end the same way if
you let them: a report that says nothing failed, because the things that would
have failed were never looked at.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

STATUSES = frozenset({"passed", "failed", "not_observed"})


class ObservationRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Observation:
    criterion_id: str
    status: str
    evidence: str = ""


@dataclass
class RunLedger:
    """What this run actually looked at, for a declared set of criteria."""

    declared: tuple[str, ...]
    observations: dict[str, Observation] = field(default_factory=dict)

    def record(self, criterion_id: str, status: str, evidence: str) -> None:
        """Record one observation. `passed` and `failed` both require evidence.

        An assertion with nothing behind it is the thing this app exists to
        refuse: it is indistinguishable from not looking, right up until
        somebody asks what the evidence was.
        """
        if criterion_id not in self.declared:
            raise ObservationRejected("undeclared_criterion", criterion_id)
        if status not in STATUSES:
            raise ObservationRejected("unknown_status", status)
        if status == "not_observed":
            raise ObservationRejected(
                "cannot_record_not_observed",
                "not_observed is the absence of a record, not a record",
            )
        if not evidence.strip():
            raise ObservationRejected("evidence_required", criterion_id)
        if criterion_id in self.observations:
            raise ObservationRejected("already_observed", criterion_id)

        self.observations[criterion_id] = Observation(criterion_id, status, evidence)

    def report(self) -> tuple[Observation, ...]:
        """One row per declared criterion, in declaration order.

        Criteria nobody observed appear as `not_observed`. They are not absent
        from the report, because absence reads as fine.
        """
        return tuple(
            self.observations.get(
                criterion_id,
                Observation(criterion_id, "not_observed", "no evidence in this run"),
            )
            for criterion_id in self.declared
        )

    def observed(self) -> tuple[int, int]:
        """(criteria with evidence, criteria declared)."""
        return len(self.observations), len(self.declared)

    def clean(self) -> bool:
        """True only if every declared criterion was observed and passed.

        Deliberately not "nothing failed". A run that looked at two of ten
        criteria and found no failures is not a clean run, and calling it one
        is how a partial pass becomes a green tick.
        """
        rows = self.report()
        return bool(rows) and all(row.status == "passed" for row in rows)


def merge(*ledgers: RunLedger) -> RunLedger:
    """Combine runs over the same declared criteria.

    Evidence accumulates across runs; a criterion observed in any run is
    observed. A disagreement between runs is refused rather than resolved,
    because picking a winner silently is how a flaky failure becomes a pass.
    """
    if not ledgers:
        raise ObservationRejected("no_ledgers", "nothing to merge")
    declared = ledgers[0].declared
    for ledger in ledgers[1:]:
        if ledger.declared != declared:
            raise ObservationRejected("declaration_mismatch", "different criteria")

    merged = RunLedger(declared=declared)
    for ledger in ledgers:
        for criterion_id, observation in ledger.observations.items():
            existing = merged.observations.get(criterion_id)
            if existing and existing.status != observation.status:
                raise ObservationRejected(
                    "conflicting_observations",
                    f"{criterion_id}: {existing.status} then {observation.status}",
                )
            merged.observations[criterion_id] = observation
    return merged

"""Grounded claim verification.

Every factual claim a model emits must name a ground-truth key that exists and
quote that record's value exactly. An uncited claim, an invented source, or an
altered quote fails closed.

This is the deterministic half of "did the model drift away from what we
know". It does not judge whether a claim is *true* — it checks whether the
claim is anchored to a record the system actually holds, and whether the value
it attributes to that record is the value the record contains. Both are string
equality, so a cheaper or degraded model cannot argue its way past the gate.
"""

from __future__ import annotations

from dataclasses import dataclass


class GroundingRejected(Exception):
    def __init__(self, reason: str, detail: str = "", claim_index: int | None = None):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail
        self.claim_index = claim_index


@dataclass(frozen=True)
class Claim:
    """One factual assertion, as the model is required to emit it."""

    text: str
    source_key: str | None
    quoted_value: str | None


class GroundTruth:
    """The records the system actually holds, keyed by a stable id."""

    def __init__(self, records: dict[str, str]):
        self._records = dict(records)

    def get(self, key: str) -> str | None:
        return self._records.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._records


def verify_claims(claims: list[Claim], ground_truth: GroundTruth) -> None:
    """Raise on the first claim that is not anchored to a held record.

    Checks run in a fixed order per claim — cited, source exists, quote
    matches — and claims are checked in order, so the same output always
    produces the same rejection.

    Quote comparison is exact. Normalizing whitespace or case here would be a
    policy decision about how much drift is acceptable, and this app
    deliberately does not make it: an exact gate can be loosened on purpose,
    while a fuzzy one can never be tightened back with confidence.
    """
    for index, claim in enumerate(claims):
        if not claim.source_key:
            raise GroundingRejected("uncited_claim", claim.text, index)

        actual = ground_truth.get(claim.source_key)
        if actual is None:
            # A citation to a key that does not exist is a fabricated source —
            # the most convincing failure mode, because it looks cited.
            raise GroundingRejected("unknown_source", claim.source_key, index)

        if claim.quoted_value != actual:
            raise GroundingRejected(
                "quote_mismatch",
                f"key={claim.source_key} quoted={claim.quoted_value!r} "
                f"actual={actual!r}",
                index,
            )

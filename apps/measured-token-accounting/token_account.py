"""Measured token accounting.

You cannot govern what you do not measure. Every model call is recorded with
usage reported by the provider; a call whose usage is missing is refused
rather than counted as zero; and the recorded parts must reconcile exactly
with the provider's own reported total.

The distinction this app is built around is `None` versus `0`. A call that
genuinely consumed nothing is measured and costs nothing. A call whose usage
never arrived is *unknown*, and silently treating unknown as zero is how a
budget drifts away from reality while still looking balanced.
"""

from __future__ import annotations

from dataclasses import dataclass


class AccountingRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
        )


ZERO_USAGE = Usage(prompt_tokens=0, completion_tokens=0)


@dataclass(frozen=True)
class CallRecord:
    call_id: str
    usage: Usage


class TokenAccount:
    """Per-call usage ledger that refuses to invent numbers it wasn't given."""

    def __init__(self):
        self._records: list[CallRecord] = []
        self._seen: set[str] = set()

    @property
    def records(self) -> list[CallRecord]:
        return self._records

    @property
    def call_count(self) -> int:
        return len(self._records)

    def record(self, call_id: str, usage: Usage | None) -> None:
        """Record one call's measured usage.

        `usage=None` means the provider reported nothing. That is refused: an
        unmeasured call is a hole in the accounting, not a free one.
        """
        if not call_id:
            raise AccountingRejected("invalid_call_id", "empty call id")
        if call_id in self._seen:
            # Double-counting is the other direction the total can drift.
            raise AccountingRejected("duplicate_call", call_id)
        if usage is None:
            raise AccountingRejected("unmeasured_call", call_id)
        if usage.prompt_tokens < 0 or usage.completion_tokens < 0:
            raise AccountingRejected("invalid_usage", call_id)

        self._seen.add(call_id)
        self._records.append(CallRecord(call_id=call_id, usage=usage))

    def total(self) -> Usage:
        running = ZERO_USAGE
        for record in self._records:
            running = running + record.usage
        return running

    def reconcile(self, provider_reported_total: Usage) -> None:
        """The sum of the parts must equal the whole the provider reports.

        A mismatch means a call happened that this account never saw — the
        failure mode a per-call ledger exists to make visible.
        """
        measured = self.total()
        if measured != provider_reported_total:
            raise AccountingRejected(
                "reconciliation_mismatch",
                f"measured={measured.total_tokens} "
                f"reported={provider_reported_total.total_tokens}",
            )

"""Repeat reliability, predeclared.

The number of attempts is fixed before the first one runs. Every attempt is
retained, and a conclusion drawn from fewer than the declared number is
refused.

The failure this closes is not fraud, it is drift. Run it again because that
one looked odd; run it once more to be sure; stop when it is green. Each step
is reasonable and the series that results measures the stopping rule rather
than the system. Declaring the count first makes stopping early a refusal
instead of a judgment call.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

MINIMUM_DECLARED = 2


class SeriesRefused(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Plan:
    """Declared before the first attempt, and frozen."""

    runs: int
    configuration: str

    def __post_init__(self) -> None:
        if self.runs < MINIMUM_DECLARED:
            # A single attempt cannot disagree with anything, so it says
            # nothing at all about repeat reliability.
            raise SeriesRefused(
                "insufficient_declaration", f"{self.runs} < {MINIMUM_DECLARED}"
            )


@dataclass(frozen=True)
class Conclusion:
    stable: bool
    outcome: str | None
    distribution: tuple[tuple[str, int], ...]
    attempts: int


@dataclass
class Series:
    plan: Plan
    attempts: list[str] = field(default_factory=list)

    def record(self, outcome: str) -> int:
        """Retain one attempt. Nothing is ever discarded or overwritten."""
        if not outcome:
            raise SeriesRefused("empty_outcome", "an attempt must record something")
        self.attempts.append(outcome)
        return len(self.attempts)

    def conclude(self) -> Conclusion:
        """Summarize, or refuse because the declared series is not complete.

        Extra attempts beyond the declared count are included rather than
        trimmed: discarding them would be the same selective stopping in
        reverse.
        """
        if len(self.attempts) < self.plan.runs:
            raise SeriesRefused(
                "series_incomplete",
                f"{len(self.attempts)} of {self.plan.runs} declared attempts",
            )

        counts = Counter(self.attempts)
        distribution = tuple(sorted(counts.items()))
        stable = len(counts) == 1

        return Conclusion(
            stable=stable,
            # An unstable series has no outcome. Reporting the majority would
            # turn "this fails one time in five" into "this passes".
            outcome=self.attempts[0] if stable else None,
            distribution=distribution,
            attempts=len(self.attempts),
        )

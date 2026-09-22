"""Bounded execution budget.

A run halts at the first action that would exceed a declared budget. The
over-budget action never executes, nothing is partially charged, and the
budget cannot be extended from inside the run.

Countable resources (tool calls, cost units, tokens) are *precharged*: the
cost is known before the action runs, so the check happens first. Wall-clock
cannot be precharged — an action's duration is not known in advance — so time
is bounded by a deadline instead: an action is refused if the clock has
already passed the deadline when it would start.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class BudgetDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Charge:
    resource: str
    amount: int


class BoundedExecutionBudget:
    """Fail-closed budget meter around a run.

    Every resource must be declared up front. An undeclared resource is denied
    rather than treated as unlimited, so adding a new cost to a run cannot
    make that cost invisible.
    """

    def __init__(
        self,
        limits: dict[str, int],
        clock: Callable[[], int] | None = None,
        deadline: int | None = None,
    ):
        for resource, limit in limits.items():
            if limit < 0:
                raise ValueError(f"limit for {resource!r} must be >= 0")
        # Copied, and never mutated afterwards: there is no method that raises
        # a limit, so a run cannot extend its own budget.
        self._limits = dict(limits)
        self._spent = {resource: 0 for resource in limits}
        self._clock = clock
        self._deadline = deadline
        self._halted_reason: str | None = None

    @property
    def halted(self) -> bool:
        return self._halted_reason is not None

    def limit(self, resource: str) -> int:
        return self._require_known(resource)

    def spent(self, resource: str) -> int:
        self._require_known(resource)
        return self._spent[resource]

    def remaining(self, resource: str) -> int:
        return self._require_known(resource) - self._spent[resource]

    def _require_known(self, resource: str) -> int:
        if resource not in self._limits:
            raise BudgetDenied("unknown_resource", resource)
        return self._limits[resource]

    def _halt(self, reason: str, detail: str) -> BudgetDenied:
        self._halted_reason = reason
        return BudgetDenied(reason, detail)

    def run(
        self,
        charge: Charge,
        action: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Charge, then run — or deny without charging and halt the run."""
        if self.halted:
            raise BudgetDenied("run_halted", self._halted_reason or "")

        limit = self._require_known(charge.resource)
        if charge.amount <= 0:
            raise BudgetDenied("invalid_amount", str(charge.amount))

        if self._deadline is not None:
            now = self._clock() if self._clock else 0
            if now >= self._deadline:
                raise self._halt(
                    "deadline_exceeded", f"now={now} deadline={self._deadline}"
                )

        spent = self._spent[charge.resource]
        if spent + charge.amount > limit:
            # Nothing is charged on the denied action: the meter still reads
            # what the run actually consumed, which is what an auditor needs.
            raise self._halt(
                "budget_exhausted",
                f"resource={charge.resource} limit={limit} spent={spent} "
                f"requested={charge.amount}",
            )

        # Charged before the action runs: a resource consumed by an action that
        # then raises is still consumed, and must not be silently refunded.
        self._spent[charge.resource] = spent + charge.amount
        return action(*args, **kwargs)

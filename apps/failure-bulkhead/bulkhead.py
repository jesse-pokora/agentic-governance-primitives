"""Failure bulkhead.

After a declared number of consecutive failures a dependency is cut off: the
breaker opens, and every subsequent call fails fast without invoking it. The
breaker closes only when an explicit probe, allowed no earlier than a declared
cooldown, actually succeeds.

The failure this prevents is not the first error. It is the thousandth: an
agent that keeps calling a dependency which is already down turns one broken
service into a queue of stuck runs, and the retries are what carry the failure
outward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class BreakerOpen(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass
class Transition:
    at: int
    to: str  # "open" or "closed"
    reason: str


@dataclass
class FailureBulkhead:
    """One dependency's breaker. Not a retry policy: it never calls anything twice."""

    threshold: int
    cooldown: int
    clock: Callable[[], int]
    state: str = "closed"
    consecutive_failures: int = 0
    opened_at: int | None = None
    history: list[Transition] = field(default_factory=list)

    def call(self, action: Callable[[], Any]) -> Any:
        """Invoke the dependency, or fail fast without touching it."""
        if self.state == "open":
            raise BreakerOpen(
                "circuit_open",
                f"opened at {self.opened_at}, cooldown {self.cooldown}",
            )

        try:
            result = action()
        except Exception:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.threshold:
                self._open("threshold_reached")
            raise

        # Consecutive means consecutive: one success clears the count. A
        # breaker that counted failures forever would eventually open on a
        # healthy dependency that had a bad minute last week.
        self.consecutive_failures = 0
        return result

    def probe(self, action: Callable[[], Any]) -> Any:
        """The only way back to closed, and only after the cooldown.

        A probe is a real call to the dependency. Closing on a timer instead
        would mean the breaker decides a service recovered without ever asking
        it.
        """
        if self.state != "open":
            raise BreakerOpen("not_open", f"state is {self.state}")

        now = self.clock()
        if self.opened_at is not None and now - self.opened_at < self.cooldown:
            raise BreakerOpen(
                "cooldown_not_elapsed",
                f"{now - self.opened_at} < {self.cooldown}",
            )

        try:
            result = action()
        except Exception:
            self._open("probe_failed")  # restarts the cooldown
            raise

        self.state = "closed"
        self.consecutive_failures = 0
        self.opened_at = None
        self.history.append(Transition(now, "closed", "probe_succeeded"))
        return result

    def _open(self, reason: str) -> None:
        self.state = "open"
        self.opened_at = self.clock()
        self.history.append(Transition(self.opened_at, "open", reason))

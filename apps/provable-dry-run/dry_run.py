"""Provable dry run.

A dry run performs no effect, and that is provable rather than promised: every
effect goes through one gate, and in dry-run mode the gate records the intent
and returns without invoking it.

The usual dry-run bug is a conditional at each call site. Miss one and the
mode is silently broken, and the miss is invisible until it writes something.
Routing every effect through a single chokepoint makes "did we honour dry run"
a property of one function instead of a property of everyone's discipline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class EffectDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class PlannedEffect:
    kind: str
    target: str
    summary: str


@dataclass
class Executor:
    """The single gate every effect passes through."""

    dry_run: bool
    planned: list[PlannedEffect] = field(default_factory=list)
    performed: list[PlannedEffect] = field(default_factory=list)

    def perform(self, effect: PlannedEffect, action: Callable[[], Any]) -> Any:
        """Record the intent always; invoke the action only when live.

        The plan is built in both modes and in the same order, so a dry run's
        output is the live run's intent — not a different code path that
        happens to print something similar.
        """
        if not effect.kind or not effect.target:
            raise EffectDenied("unattributed_effect", f"{effect.kind!r}/{effect.target!r}")

        self.planned.append(effect)
        if self.dry_run:
            return None

        result = action()
        self.performed.append(effect)
        return result

    @property
    def plan(self) -> list[str]:
        return [f"{e.kind} {e.target}: {e.summary}" for e in self.planned]

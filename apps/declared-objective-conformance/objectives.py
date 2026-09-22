"""Declared objective conformance.

Every action an agent takes must cite an objective declared for the run. An
action citing nothing, or citing an objective that was never declared, is
refused before it executes — and the declared set is frozen at the start, so a
run cannot widen its own remit.

This is goal drift made checkable. An agent does not usually go off-mission by
announcing it; it takes one reasonable-looking action that serves a purpose
nobody asked for. Requiring each action to name the objective it serves turns
that into a refusal instead of a surprise in the log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class ObjectiveViolation(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Action:
    name: str
    serves: tuple[str, ...]  # the objectives this action claims to advance


@dataclass
class Run:
    """A run with a frozen set of objectives and a record of what served them."""

    objectives: frozenset[str]
    performed: list[Action] = field(default_factory=list)

    @classmethod
    def declaring(cls, objectives: set[str]) -> Run:
        if not objectives:
            raise ObjectiveViolation("no_objectives", "a run must declare at least one")
        # Copied into a frozenset: a caller that later mutates the set it
        # passed in cannot widen the run's remit from outside.
        return cls(objectives=frozenset(objectives))

    def perform(self, action: Action, do: Callable[[], Any]) -> Any:
        """Run the action only if every objective it cites was declared."""
        if not action.serves:
            raise ObjectiveViolation("uncited_action", action.name)

        undeclared = tuple(sorted(set(action.serves) - self.objectives))
        if undeclared:
            # All of them, not just the first: an action citing two undeclared
            # objectives has drifted twice, and both are worth seeing.
            raise ObjectiveViolation(
                "undeclared_objective", f"{action.name} cites {', '.join(undeclared)}"
            )

        result = do()
        self.performed.append(action)
        return result

    def objectives_served(self) -> frozenset[str]:
        """Which declared objectives anything actually advanced.

        Declared-but-unserved is not a violation — a run may find an objective
        needs no action — but it is worth being able to ask.
        """
        return frozenset(o for action in self.performed for o in action.serves)

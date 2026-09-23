"""Falsifiable instruction check.

An instruction may be registered only if its own checker rejects the violating
fixture it ships and accepts the satisfying one. A checker that cannot
discriminate between the two is refused at registration.

A policy full of checkers that never fire reports total compliance and means
nothing, and it is the easiest possible thing to build by accident: a checker
with a subtly wrong pattern passes every artifact, forever, silently. Making
each instruction prove its checker can fail turns that from an invisible
condition into a registration error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class NotFalsifiable(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Candidate:
    """An instruction offered for registration, with the evidence it must pass.

    `check` returns True when the artifact satisfies the instruction.
    `violating` must be rejected; `satisfying` must be accepted.
    """

    id: str
    text: str
    check: Callable[[Any], bool]
    violating: Any = None
    satisfying: Any = None


@dataclass(frozen=True)
class Instruction:
    id: str
    text: str
    check: Callable[[Any], bool]
    violating: Any
    satisfying: Any


def _run(check: Callable[[Any], bool], fixture: Any, which: str, id: str) -> bool:
    try:
        return bool(check(fixture))
    except Exception as error:
        raise NotFalsifiable(
            "checker_errored", f"{id} raised {type(error).__name__} on its {which} fixture"
        ) from None


def register(candidate: Candidate) -> Instruction:
    """Admit the instruction, or refuse it with the reason it is not testable."""
    if candidate.violating is None:
        # Without one, there is no way to tell a strict checker from a stub.
        raise NotFalsifiable("missing_violating_fixture", candidate.id)
    if candidate.satisfying is None:
        raise NotFalsifiable("missing_satisfying_fixture", candidate.id)

    if _run(candidate.check, candidate.violating, "violating", candidate.id):
        raise NotFalsifiable(
            "checker_accepts_violation",
            f"{candidate.id} passes an artifact it is supposed to reject",
        )
    if not _run(candidate.check, candidate.satisfying, "satisfying", candidate.id):
        raise NotFalsifiable(
            "checker_rejects_satisfying",
            f"{candidate.id} fails an artifact it is supposed to accept",
        )

    return Instruction(
        id=candidate.id,
        text=candidate.text,
        check=candidate.check,
        violating=candidate.violating,
        satisfying=candidate.satisfying,
    )


@dataclass
class Registry:
    instructions: dict[str, Instruction] = field(default_factory=dict)

    def add(self, candidate: Candidate) -> Instruction:
        if candidate.id in self.instructions:
            raise NotFalsifiable("duplicate_instruction_id", candidate.id)
        instruction = register(candidate)
        self.instructions[candidate.id] = instruction
        return instruction

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.instructions))

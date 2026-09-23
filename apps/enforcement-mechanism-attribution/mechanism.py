"""Enforcement mechanism attribution.

A result that does not name the mechanism enforcing an instruction cannot be
compared with one that does. The same instruction delivered as prose, as a
skill, as a hook, as a gate or by the host produces different adherence, and a
result that omits which one was in effect is not a data point about the
instruction — it is a data point about an unknown.

This is the difference between "the instruction works" and "the instruction
works when a gate enforces it". Only the second tells you what to build.
"""

from __future__ import annotations

from dataclasses import dataclass

# Ordered weakest to strongest by how much the agent must cooperate.
MECHANISMS = ("prose", "skill", "hook", "gate", "host")


class Incomparable(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Result:
    run_id: str
    instruction_id: str
    mechanism: str | None
    followed: bool


@dataclass(frozen=True)
class Comparison:
    instruction_id: str
    weaker: str
    stronger: str
    verdict: str  # "stronger_mechanism_helped", "no_difference", "weaker_sufficed"


def record(run_id: str, instruction_id: str, mechanism: str | None,
           followed: bool) -> Result:
    """Record one observation, refusing a mechanism outside the vocabulary.

    `None` is allowed and is not the same as a missing field: it says the
    mechanism was not recorded, which is a fact the comparison will act on.
    """
    if mechanism is not None and mechanism not in MECHANISMS:
        raise Incomparable("unknown_mechanism", mechanism)
    return Result(run_id, instruction_id, mechanism, followed)


def compare(first: Result, second: Result) -> Comparison:
    """Compare two results for the same instruction under different mechanisms."""
    if first.instruction_id != second.instruction_id:
        raise Incomparable(
            "different_instructions",
            f"{first.instruction_id} vs {second.instruction_id}",
        )
    for result in (first, second):
        if result.mechanism is None:
            raise Incomparable("mechanism_not_recorded", result.run_id)
    if first.mechanism == second.mechanism:
        raise Incomparable(
            "same_mechanism",
            f"both {first.mechanism}; this compares runs, not mechanisms",
        )

    ordered = sorted((first, second), key=lambda r: MECHANISMS.index(r.mechanism))
    weaker, stronger = ordered

    if weaker.followed and stronger.followed:
        verdict = "weaker_sufficed"
    elif stronger.followed and not weaker.followed:
        verdict = "stronger_mechanism_helped"
    else:
        verdict = "no_difference"

    return Comparison(first.instruction_id, weaker.mechanism, stronger.mechanism, verdict)

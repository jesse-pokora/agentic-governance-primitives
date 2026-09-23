"""Ablation required for a causal claim.

A finding may be recorded as *caused by* an instruction only when a leave-one-out
comparison exists: two runs identical in every declared factor except that
instruction. Without one the finding is still recorded — as a correlation.

The default diagnosis is the dangerous one. An agent produced a bad outcome and
an instruction was violated, so the violation caused the outcome. Usually
nobody checks whether removing the instruction changes anything, and the
instruction earns permanent residency in a prompt on the strength of a
coincidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class AttributionRefused(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Run:
    """One observed run: the factors that were in effect, and what happened."""

    id: str
    instructions: frozenset[str]
    factors: tuple[tuple[str, str], ...]  # task, model, corpus, temperature...
    outcome: str

    @classmethod
    def of(cls, id: str, instructions: set[str], factors: dict[str, str],
           outcome: str) -> Run:
        return cls(id, frozenset(instructions), tuple(sorted(factors.items())), outcome)


@dataclass
class Finding:
    instruction_id: str
    relation: str  # "caused", "correlated", or "no_effect"
    detail: str
    compared: tuple[str, ...] = field(default_factory=tuple)


def attribute(instruction_id: str, treatment: Run, control: Run | None = None) -> Finding:
    """Relate an instruction to an outcome, at the strength the evidence allows.

    `control` is the leave-one-out run. With none, the result is a correlation
    — which is recorded rather than discarded, because an observed omission is
    still worth knowing; it just is not a cause.
    """
    if instruction_id not in treatment.instructions:
        raise AttributionRefused(
            "instruction_absent_from_treatment",
            f"{instruction_id} was not in effect during {treatment.id}",
        )

    if control is None:
        return Finding(
            instruction_id,
            "correlated",
            "no leave-one-out run; the outcome was observed alongside this "
            "instruction, not shown to follow from it",
            (treatment.id,),
        )

    if instruction_id in control.instructions:
        raise AttributionRefused(
            "control_retains_instruction",
            f"{instruction_id} is still in effect in {control.id}",
        )

    # Everything except the one instruction must match, or the comparison
    # cannot say which difference did the work.
    if treatment.factors != control.factors:
        differing = sorted(
            key for key, value in treatment.factors
            if dict(control.factors).get(key) != value
        ) or sorted(key for key, _ in control.factors if key not in dict(treatment.factors))
        raise AttributionRefused("confounded_comparison", ", ".join(differing))

    removed = treatment.instructions - control.instructions
    if removed != {instruction_id}:
        raise AttributionRefused(
            "multiple_instructions_removed", ", ".join(sorted(removed))
        )

    if treatment.outcome == control.outcome:
        return Finding(
            instruction_id,
            "no_effect",
            f"outcome was {treatment.outcome!r} with and without it",
            (treatment.id, control.id),
        )

    return Finding(
        instruction_id,
        "caused",
        f"{control.outcome!r} without it, {treatment.outcome!r} with it",
        (treatment.id, control.id),
    )

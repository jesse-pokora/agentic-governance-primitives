"""Non-overlapping validation-stage error mapping.

Every input reaches exactly one named validation stage and, if it fails,
exactly one named error — never two, never zero. Stages are checked in a
fixed order and the first match short-circuits, and a final catch-all stage
guarantees every input is classified somewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

Fixture = dict


@dataclass(frozen=True)
class Stage:
    name: str
    error_name: str | None  # None marks the terminal "valid" stage
    predicate: Callable[[Fixture], bool]


@dataclass(frozen=True)
class Outcome:
    stage: str
    error: str | None


def _has_required_id(fixture: Fixture) -> bool:
    return "id" not in fixture


def _amount_wrong_type(fixture: Fixture) -> bool:
    return not isinstance(fixture.get("amount"), (int, float)) or isinstance(
        fixture.get("amount"), bool
    )


def _amount_out_of_range(fixture: Fixture) -> bool:
    amount = fixture.get("amount")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        return False  # not this stage's concern; the type stage owns that case
    return amount < 0


STAGES: list[Stage] = [
    Stage("schema", "missing_required_id", _has_required_id),
    Stage("type", "amount_wrong_type", _amount_wrong_type),
    Stage("range", "amount_out_of_range", _amount_out_of_range),
    Stage("terminal", None, lambda fixture: True),  # catch-all: guarantees never zero
]


def classify(fixture: Fixture) -> Outcome:
    for stage in STAGES:
        if stage.predicate(fixture):
            return Outcome(stage=stage.name, error=stage.error_name)
    raise AssertionError("unreachable: terminal stage always matches")

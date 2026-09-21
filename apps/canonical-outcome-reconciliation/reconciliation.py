"""Canonical outcome reconciliation.

Every input key in a batch receives exactly one attributable success or
failure outcome, in a fixed order — nothing silently dropped, nothing
double-counted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Outcome:
    key: str
    status: str  # "success" | "failure"
    detail: Any


def reconcile(batch: dict[str, Callable[[], Any]]) -> list[Outcome]:
    """Attempt every key's action exactly once, in the batch's insertion
    order, and return exactly one Outcome per key in that same order.
    """
    outcomes: list[Outcome] = []
    for key, action in batch.items():
        try:
            result = action()
        except Exception as exc:
            outcomes.append(Outcome(key=key, status="failure", detail=str(exc)))
        else:
            outcomes.append(Outcome(key=key, status="success", detail=result))

    assert [o.key for o in outcomes] == list(batch.keys())
    return outcomes

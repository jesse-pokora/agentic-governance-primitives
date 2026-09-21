"""Governed preflight denial evidence.

When a precondition check fails, the system emits a fixed-shape,
allowlisted-field denial record — never the raw exception text, which may
contain absolute paths, secrets, or other sensitive detail.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

ALLOWED_FIELDS = frozenset({"denied", "reason_code", "precondition"})

# Fixed vocabulary — never derived from the raw exception message.
REASON_CODE_PRECONDITION_FAILED = "precondition_failed"


@dataclass(frozen=True)
class DenialRecord:
    denied: bool
    reason_code: str
    precondition: str

    def to_dict(self) -> dict:
        record = {
            "denied": self.denied,
            "reason_code": self.reason_code,
            "precondition": self.precondition,
        }
        assert set(record.keys()) == ALLOWED_FIELDS
        return record


def run_preflight(precondition_name: str, check_fn: Callable[[], None]) -> DenialRecord | None:
    """Run check_fn. Return None if it passes.

    If it raises anything, the exception (and whatever sensitive detail it
    carries) is discarded — only a fixed-shape DenialRecord is produced.
    """
    try:
        check_fn()
        return None
    except Exception:
        return DenialRecord(
            denied=True,
            reason_code=REASON_CODE_PRECONDITION_FAILED,
            precondition=precondition_name,
        )

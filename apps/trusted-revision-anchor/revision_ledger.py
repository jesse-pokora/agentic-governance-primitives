"""Trusted revision anchor.

The "current" commit is selected only from a ledger slot position, never
from caller-supplied input. "Fresh" means "at the ledger head," not
"recent by clock time" — there is no timestamp anywhere in this API.
"""

from __future__ import annotations


class NoRevisionsRecorded(Exception):
    pass


class RevisionLedger:
    """An append-only, position-only ledger of commit ids.

    Deliberately has no method that accepts a caller-supplied "current" or
    "preferred" commit — `current()` takes no arguments at all.
    """

    def __init__(self):
        self._slots: list[str] = []

    def record(self, commit_id: str) -> int:
        """Append commit_id and return its slot position."""
        self._slots.append(commit_id)
        return len(self._slots) - 1

    def current(self) -> str:
        """The ledger head — the only definition of 'current' this API has."""
        if not self._slots:
            raise NoRevisionsRecorded("no_revisions_recorded")
        return self._slots[-1]

    def is_fresh(self, commit_id: str) -> bool:
        """True only if commit_id is at the ledger head right now.

        Not based on when commit_id was recorded, how long ago that was, or
        any wall-clock notion of "recent" — none of that exists here.
        """
        return bool(self._slots) and self._slots[-1] == commit_id

    def slot_position(self, commit_id: str) -> int | None:
        try:
            return self._slots.index(commit_id)
        except ValueError:
            return None

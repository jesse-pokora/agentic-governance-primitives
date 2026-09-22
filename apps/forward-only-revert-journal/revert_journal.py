"""Forward-only revert journal.

A revert is recorded as a new forward record naming the state it left behind —
history is appended, never rewritten. The state that was abandoned is still
readable from the journal afterwards, which is exactly the part a destructive
revert deletes.

Every record carries the digest that was in effect *before* it, so removing or
reordering a record breaks the linkage and is detected.
"""

from __future__ import annotations

from dataclasses import dataclass


class JournalRejected(Exception):
    def __init__(self, reason: str, detail: str = "", index: int | None = None):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail
        self.index = index


@dataclass(frozen=True)
class Record:
    index: int
    kind: str  # "set" or "revert"
    digest: str  # the state in effect after this record
    from_digest: str | None  # the state in effect before it


class ForwardOnlyRevertJournal:
    """Append-only history of which state held, and when.

    There is no method that removes or edits a record. `verify()` exists for
    the case where something bypasses that and edits the list directly.
    """

    def __init__(self):
        self._records: list[Record] = []

    @property
    def records(self) -> list[Record]:
        return self._records

    @property
    def current_digest(self) -> str | None:
        return self._records[-1].digest if self._records else None

    def digests_that_held(self) -> list[str]:
        """Every state that was ever in effect, in the order it took effect."""
        return [record.digest for record in self._records]

    def _append(self, kind: str, digest: str) -> int:
        record = Record(
            index=len(self._records),
            kind=kind,
            digest=digest,
            from_digest=self.current_digest,
        )
        self._records.append(record)
        return record.index

    def set_state(self, digest: str) -> int:
        """Record a new state taking effect."""
        return self._append("set", digest)

    def revert_to(self, digest: str) -> int:
        """Record a revert to a state that previously held.

        Reverting to a state that never held is refused: a "revert" to
        something the system was never in is a new state wearing the word
        revert, and should be recorded as one.
        """
        if not self._records:
            raise JournalRejected("no_history", "nothing has taken effect yet")
        if digest not in self.digests_that_held():
            raise JournalRejected("never_held", digest)
        return self._append("revert", digest)

    def verify(self) -> None:
        """Detect a history that was rewritten rather than appended to.

        Each record names the digest in effect before it, so deleting,
        reordering, or inserting a record breaks the linkage at that point.
        """
        in_effect: str | None = None
        seen: set[str] = set()

        for position, record in enumerate(self._records):
            if record.index != position:
                raise JournalRejected(
                    "index_not_contiguous", f"record.index={record.index}", position
                )
            if record.from_digest != in_effect:
                raise JournalRejected(
                    "history_rewritten",
                    f"from_digest={record.from_digest} in_effect={in_effect}",
                    position,
                )
            if record.kind == "revert" and record.digest not in seen:
                raise JournalRejected("never_held", record.digest, position)

            seen.add(record.digest)
            in_effect = record.digest

"""Memory conflict quarantine.

When two memory records assert different values for the same key, both are
retained and the conflict is surfaced — the newer one never silently
overwrites the older.

Last-write-wins is the default in almost every store, and it is the wrong
default for agent memory: the newer record is not more trustworthy for being
newer, and a model that drifts writes its drift *last*. Quarantining the
conflict turns a silent overwrite into something a human or a policy has to
resolve on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass


class MemoryRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class MemoryRecord:
    key: str
    value: str
    source: str  # who asserted it — never dropped, so a conflict is attributable


@dataclass(frozen=True)
class Conflict:
    key: str
    held: MemoryRecord
    incoming: MemoryRecord


class QuarantiningMemoryStore:
    """Agent memory in which a contradiction is an event, not an overwrite."""

    def __init__(self):
        self._settled: dict[str, MemoryRecord] = {}
        self._quarantine: list[Conflict] = []

    @property
    def quarantine(self) -> list[Conflict]:
        return self._quarantine

    def settled_keys(self) -> list[str]:
        return sorted(self._settled)

    def read(self, key: str) -> MemoryRecord:
        """Return the settled record, or refuse if the key is in conflict.

        A key under conflict has no answer. Returning either side would be the
        silent choice this store exists to avoid.
        """
        if any(conflict.key == key for conflict in self._quarantine):
            raise MemoryRejected("key_in_conflict", key)
        record = self._settled.get(key)
        if record is None:
            raise MemoryRejected("unknown_key", key)
        return record

    def write(self, record: MemoryRecord) -> bool:
        """Write a record. Returns True if settled, False if quarantined.

        An identical re-assertion is not a conflict — the same value from a
        different source is corroboration, and is allowed to settle.
        """
        held = self._settled.get(record.key)
        if held is None:
            self._settled[record.key] = record
            return True

        if held.value == record.value:
            return True

        self._quarantine.append(
            Conflict(key=record.key, held=held, incoming=record)
        )
        return False

    def resolve(self, key: str, chosen: MemoryRecord) -> None:
        """Settle a conflicted key by explicitly choosing a value.

        The chosen value must be one of the values actually in conflict:
        resolution is a decision between what was asserted, not a chance to
        write a third thing without a record of it.
        """
        conflicts = [c for c in self._quarantine if c.key == key]
        if not conflicts:
            raise MemoryRejected("not_in_conflict", key)
        if chosen.key != key:
            raise MemoryRejected("key_mismatch", f"{chosen.key} != {key}")

        asserted = {c.held.value for c in conflicts} | {c.incoming.value for c in conflicts}
        if chosen.value not in asserted:
            raise MemoryRejected("value_never_asserted", chosen.value)

        self._settled[key] = chosen
        self._quarantine = [c for c in self._quarantine if c.key != key]

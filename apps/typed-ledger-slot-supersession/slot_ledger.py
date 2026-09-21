"""Typed ledger-slot supersession.

A later record can only replace an earlier one by naming that exact slot
key *and* the exact digest of the record it's replacing. A fork (wrong
digest) or a missing predecessor (unknown slot) fails closed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


def _canonical_json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest_of(value: dict) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class SupersessionDenied(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class SlotRecord:
    slot_key: str
    value: dict
    digest: str


class TypedLedgerSlots:
    def __init__(self):
        self._slots: dict[str, SlotRecord] = {}

    def get(self, slot_key: str) -> SlotRecord | None:
        return self._slots.get(slot_key)

    def create(self, slot_key: str, value: dict) -> SlotRecord:
        if slot_key in self._slots:
            raise SupersessionDenied("slot_already_exists")
        record = SlotRecord(slot_key=slot_key, value=dict(value), digest=digest_of(value))
        self._slots[slot_key] = record
        return record

    def supersede(self, slot_key: str, expected_predecessor_digest: str, new_value: dict) -> SlotRecord:
        current = self._slots.get(slot_key)
        if current is None:
            raise SupersessionDenied("missing_predecessor")
        if current.digest != expected_predecessor_digest:
            # Either a genuine fork (someone built on a different version of
            # this slot) or a stale caller replaying an old digest.
            raise SupersessionDenied("predecessor_digest_mismatch")

        record = SlotRecord(
            slot_key=slot_key, value=dict(new_value), digest=digest_of(new_value)
        )
        self._slots[slot_key] = record
        return record

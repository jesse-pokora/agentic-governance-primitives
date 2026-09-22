"""Concurrent append integrity.

Under concurrent writers an append-only ledger admits exactly one entry per
accepted append, with strictly increasing indices and an unbroken hash chain.
A writer whose predecessor changed under it is rejected outright rather than
silently reordered or overwritten.

Two disciplines are shown, plus the hazard they exist to prevent:

- `append_unsafe` — no coordination. Present only to demonstrate that the
  hazard is real; the chain it produces does not verify.
- `append_cas`    — optimistic: the caller names the head it built on, and a
                    changed head rejects the append.
- `append_locked` — pessimistic: the head is read and extended under one lock.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass

GENESIS_HASH = "0" * 64


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class ConcurrentAppendRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Entry:
    index: int
    prev_hash: str
    payload: dict
    entry_hash: str


@dataclass
class VerificationResult:
    valid: bool
    first_bad_index: int | None = None
    reason: str | None = None


def entry_hash_for(prev_hash: str, payload: dict) -> str:
    return hashlib.sha256(
        (prev_hash + canonical_json(payload)).encode("utf-8")
    ).hexdigest()


class ConcurrentLedger:
    def __init__(self):
        self._entries: list[Entry] = []
        self._lock = threading.Lock()

    @property
    def entries(self) -> list[Entry]:
        return self._entries

    def head_hash(self) -> str:
        return self._entries[-1].entry_hash if self._entries else GENESIS_HASH

    def _build(self, payload: dict, prev_hash: str) -> Entry:
        return Entry(
            index=len(self._entries),
            prev_hash=prev_hash,
            payload=dict(payload),
            entry_hash=entry_hash_for(prev_hash, payload),
        )

    def append_unsafe(self, payload: dict, prev_hash: str) -> int:
        """Append against a caller-supplied predecessor, no questions asked.

        This is the hazard, kept executable so the tests can show it rather
        than assert it in prose.
        """
        entry = self._build(payload, prev_hash)
        self._entries.append(entry)
        return entry.index

    def append_cas(self, payload: dict, expected_head: str) -> int:
        """Append only if the head is still what the caller built on."""
        with self._lock:
            actual_head = self.head_hash()
            if actual_head != expected_head:
                raise ConcurrentAppendRejected(
                    "head_moved", f"expected={expected_head} actual={actual_head}"
                )
            entry = self._build(payload, actual_head)
            self._entries.append(entry)
            return entry.index

    def append_locked(self, payload: dict) -> int:
        """Read the head and extend it under one lock — serialized, never lost."""
        with self._lock:
            entry = self._build(payload, self.head_hash())
            self._entries.append(entry)
            return entry.index

    def verify(self) -> VerificationResult:
        expected_prev = GENESIS_HASH
        for position, entry in enumerate(self._entries):
            if entry.index != position:
                return VerificationResult(False, position, "index_not_contiguous")
            if entry.prev_hash != expected_prev:
                return VerificationResult(False, position, "chain_broken")
            if entry_hash_for(entry.prev_hash, entry.payload) != entry.entry_hash:
                return VerificationResult(False, position, "hash_mismatch")
            expected_prev = entry.entry_hash
        return VerificationResult(True)

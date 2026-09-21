"""Authenticated transition ledger.

An append-only, SHA-256-chained, HMAC-signed event log. Verification walks
the whole chain, so a single edited byte anywhere in history — not just the
tampered row — is detected.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field

GENESIS_HASH = "0" * 64


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass
class LedgerEntry:
    index: int
    prev_hash: str
    payload: dict
    entry_hash: str
    hmac_sig: str


@dataclass
class VerificationResult:
    valid: bool
    first_bad_index: int | None = None
    reason: str | None = None


class AuthenticatedTransitionLedger:
    def __init__(self, secret_key: bytes):
        self._secret_key = secret_key
        self._entries: list[LedgerEntry] = []

    @property
    def entries(self) -> list[LedgerEntry]:
        return self._entries

    def _compute_entry_hash(self, prev_hash: str, payload: dict) -> str:
        return hashlib.sha256(
            (prev_hash + canonical_json(payload)).encode("utf-8")
        ).hexdigest()

    def _compute_hmac(self, index: int, prev_hash: str, entry_hash: str) -> str:
        message = f"{index}|{prev_hash}|{entry_hash}".encode("utf-8")
        return hmac.new(self._secret_key, message, hashlib.sha256).hexdigest()

    def append(self, payload: dict) -> int:
        prev_hash = self._entries[-1].entry_hash if self._entries else GENESIS_HASH
        index = len(self._entries)
        entry_hash = self._compute_entry_hash(prev_hash, payload)
        hmac_sig = self._compute_hmac(index, prev_hash, entry_hash)
        self._entries.append(
            LedgerEntry(
                index=index,
                prev_hash=prev_hash,
                payload=dict(payload),
                entry_hash=entry_hash,
                hmac_sig=hmac_sig,
            )
        )
        return index

    def verify(self) -> VerificationResult:
        expected_prev_hash = GENESIS_HASH
        for entry in self._entries:
            if entry.prev_hash != expected_prev_hash:
                return VerificationResult(
                    valid=False, first_bad_index=entry.index, reason="chain_broken"
                )

            recomputed_entry_hash = self._compute_entry_hash(
                entry.prev_hash, entry.payload
            )
            if recomputed_entry_hash != entry.entry_hash:
                return VerificationResult(
                    valid=False, first_bad_index=entry.index, reason="hash_mismatch"
                )

            recomputed_hmac = self._compute_hmac(
                entry.index, entry.prev_hash, entry.entry_hash
            )
            if not hmac.compare_digest(recomputed_hmac, entry.hmac_sig):
                return VerificationResult(
                    valid=False, first_bad_index=entry.index, reason="hmac_mismatch"
                )

            expected_prev_hash = entry.entry_hash

        return VerificationResult(valid=True)

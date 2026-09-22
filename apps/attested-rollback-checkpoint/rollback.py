"""Attested rollback checkpoint.

A rollback restores exactly a previously attested state digest — it fails
closed if the target was never attested, or if the bytes filed under that
digest no longer re-hash to it.

Recording *that* a rollback happened is a separate rule with its own app: see
../forward-only-revert-journal.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def digest_of(state: dict) -> str:
    return hashlib.sha256(canonical_json(state).encode("utf-8")).hexdigest()


class RollbackDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


class AttestedCheckpointStore:
    """Content-addressed store of states that are legal rollback targets."""

    def __init__(self):
        self._by_digest: dict[str, str] = {}  # digest -> canonical bytes
        self._current_digest: str | None = None

    @property
    def current_digest(self) -> str | None:
        return self._current_digest

    @property
    def attested_digests(self) -> frozenset[str]:
        return frozenset(self._by_digest)

    def attest(self, state: dict) -> str:
        """Record a state as a legal rollback target and return its digest.

        Content-addressed, so attesting an identical state twice returns the
        same digest and stores no second copy.
        """
        serialized = canonical_json(state)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self._by_digest[digest] = serialized
        self._current_digest = digest
        return digest

    def rollback(self, target_digest: str) -> dict:
        """Restore an attested state, or refuse.

        Two independent checks:

        1. The target must have been attested here. An arbitrary digest — even
           the correct digest of a state that genuinely exists elsewhere — is
           refused. "Restore whatever the caller names" is an unaudited write
           with a friendly name.
        2. The bytes filed under that digest must still hash to it. This
           catches a corrupted or substituted checkpoint, where trusting the
           index alone would hand back the wrong state *under a trusted name*.
        """
        if not self._by_digest:
            raise RollbackDenied("no_checkpoints", "nothing has been attested")

        serialized = self._by_digest.get(target_digest)
        if serialized is None:
            raise RollbackDenied("unattested_target", target_digest)

        actual = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        if actual != target_digest:
            raise RollbackDenied(
                "restored_digest_mismatch", f"filed={target_digest} actual={actual}"
            )

        self._current_digest = target_digest
        return json.loads(serialized)

"""Execution lock and recovery.

A crashed run leaves a lock that only an explicit, challenge-authenticated
operator attestation can clear. There is no liveness check, no timeout, and
no code path that infers a run is dead on its own.
"""

from __future__ import annotations

import secrets


class LockHeld(Exception):
    def __init__(self, run_id: str):
        super().__init__(f"lock_held: run_id={run_id}")
        self.run_id = run_id


class RecoveryDenied(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class ExecutionLockManager:
    """In-memory stand-in for a lock file. No clock, no PID table, no
    liveness inference of any kind — deliberately, so there is no code path
    that could clear a lock without an explicit matching challenge.
    """

    def __init__(self):
        self._locks: dict[str, str] = {}

    def is_locked(self, run_id: str) -> bool:
        return run_id in self._locks

    def acquire(self, run_id: str) -> str:
        """Acquire the lock for run_id, returning a one-time challenge.

        Raises LockHeld if the run is already locked — even if the process
        that acquired it has since crashed; this manager has no way to know
        that, and does not try to guess.
        """
        if run_id in self._locks:
            raise LockHeld(run_id)
        challenge = secrets.token_hex(16)
        self._locks[run_id] = challenge
        return challenge

    def clear(self, run_id: str, attested_challenge: str) -> None:
        """Clear the lock only if attested_challenge exactly matches the one
        issued at acquire() time. This is the only way a lock is ever
        cleared — there is no expiry and no automatic recovery path.
        """
        stored = self._locks.get(run_id)
        if stored is None:
            raise RecoveryDenied("no_lock_held")
        if attested_challenge != stored:
            raise RecoveryDenied("challenge_mismatch")
        del self._locks[run_id]

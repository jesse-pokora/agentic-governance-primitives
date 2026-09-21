# execution-lock-and-recovery

**Atomic claim:** A crashed run leaves a lock that only an explicit,
challenge-authenticated operator attestation can clear — the system never
infers liveness on its own.

**Inspired by:** reservation-recovery endpoints (named for context; this
app does not import or depend on that source).

**Enforcement class:** deterministic — clearing a lock is a binary exact
string comparison against a one-time challenge, with no other code path.

## How it works

`ExecutionLockManager.acquire(run_id)` locks a run and returns a random
one-time `challenge`. A second `acquire()` for the same `run_id` always
raises `LockHeld` — even if the original process crashed, since this
manager has no clock, PID table, or heartbeat and makes no attempt to guess
whether the run is still alive.

`clear(run_id, attested_challenge)` is the *only* way a lock is released,
and only succeeds if `attested_challenge` exactly equals the challenge
issued at `acquire()` time. There is no expiry and no "looks dead, clear
it" path — recovery always requires an operator to produce the exact
challenge, standing in for an out-of-band attestation.

## Run it

```bash
cd apps/execution-lock-and-recovery
python -m unittest test_lock_manager.py -v
```

One test enumerates the class's public API to confirm no
liveness-inference or timeout-based method exists at all.

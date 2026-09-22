# attested-rollback-checkpoint

**Atomic claim:** A rollback restores exactly a previously attested state
digest — it fails closed if the target was never attested or if the stored
bytes no longer re-hash to it — and it appends to history rather than erasing
it.

**Inspired by:** attested checkpoint/compensating-action contracts in governed
change systems (named for context; this app does not import or depend on any
other source). This is a v1.1 gap-closure app: the catalog could prove what
happened and stop what shouldn't, and nothing could get a run *back* to a
known-good state under the same discipline.

**Enforcement class:** deterministic — SHA-256 equality against an
append-only journal of attested states.

## How it works

`attest(state)` canonicalizes the state, files its bytes under their SHA-256,
and appends an `attest` record. `rollback(target_digest)` makes two
independent checks before restoring anything:

1. **The target must have been attested.** An arbitrary digest — even the
   correct digest of a state that genuinely exists elsewhere — is refused as
   `unattested_target`. "Roll back to whatever the caller names" is not a
   rollback; it is an unaudited write with a friendly name.
2. **The stored bytes must still hash to the digest they were filed under.**
   This catches a corrupted or substituted checkpoint. Trusting the index
   alone would hand back the wrong state *under a trusted name*, which is
   worse than failing.

The third property is the one that makes this governance rather than an undo
button: **a rollback is a forward record.** The journal gains a `rollback`
record naming both the restored digest and the `from_digest` it left behind;
nothing is removed. Rolling "forward" again is simply another rollback record.
An auditor reading the journal can still see the state that was abandoned and
when — which is exactly the part a destructive revert deletes.

Attestation is content-addressed, so attesting an identical state twice
returns the same digest and creates no second copy.

## Run it

```bash
cd apps/attested-rollback-checkpoint
python -m unittest test_rollback.py -v
```

All seven tests use toy config states (no real deployment or infrastructure):
a clean rollback, an unattested target, a corrupted checkpoint, an empty
store, history being appended rather than erased, rolling forward again, and
content-addressed re-attestation. The corruption test writes to the store's
private `_by_digest` map directly — that is the only way to stage the exact
failure the second check exists for.

# typed-ledger-slot-supersession

**Atomic claim:** A later record can only replace an earlier one by naming
that exact slot key *and* the exact digest of the record it's replacing —
a fork or missing predecessor fails closed.

**Inspired by:** typed ledger-slot approval/retention authority (named for
context; this app does not import or depend on that source).

**Enforcement class:** deterministic — supersession is a binary exact
digest comparison against the slot's current record.

## How it works

`TypedLedgerSlots.create(slot_key, value)` stores a `SlotRecord` with a
SHA-256 `digest` of its canonical JSON value. `supersede(slot_key,
expected_predecessor_digest, new_value)` only replaces the slot if:

1. the slot already exists (a `missing_predecessor` fixed-vocabulary
   denial otherwise), and
2. its **current** digest exactly equals `expected_predecessor_digest`
   (a `predecessor_digest_mismatch` denial otherwise — covering both a
   genuine fork and a stale caller replaying an old generation's digest).

Because the check is against the slot's *current* digest rather than any
digest ever seen, once a slot has moved to generation N, only a caller who
names generation N's exact digest can move it to N+1 — a caller stuck on
generation N-1's digest is rejected rather than silently rewinding state.

## Run it

```bash
cd apps/typed-ledger-slot-supersession
python -m unittest test_slot_ledger.py -v
```

Slot values (`{"version": 1}`) are toy placeholders for whatever typed
record a real system would store.

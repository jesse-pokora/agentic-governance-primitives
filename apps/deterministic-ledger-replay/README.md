# deterministic-ledger-replay

**Atomic claim:** Replaying a ledger from genesis reproduces its state
byte-for-byte, and any state the replay cannot reproduce is rejected — with
the first divergent event named.

**Inspired by:** event-sourced state reconstruction in auditable systems
(named for context; this app does not import or depend on any other source).
This is a v1.1 gap-closure app:
[authenticated-transition-ledger](../authenticated-transition-ledger) proves
the *log* is intact, and nothing proved the *state* was derivable from it.

**Enforcement class:** deterministic — pure reducers over canonical JSON
digests; no wall-clock, no randomness, no iteration-order dependence.

## How it works

Events are typed, and each type has a pure reducer `(state, payload) -> state`
that never mutates its input. `replay(events)` folds them over
`GENESIS_STATE`, recording a digest after each one; `ReplayableLedger.append`
does the same incrementally and stores `state_digest_after` on every entry.

`verify()` replays from genesis and rejects two distinct failures:

- **`checkpoint_divergence`** — a recorded checkpoint the replay disagrees
  with, pinpointed to the *first* divergent index. That index is the answer to
  "when did state go wrong", which a single final-digest comparison can't give.
- **`state_not_derivable`** — the live state is not the replay's final state.
  That is the signature of a write that bypassed the log entirely, which is
  the failure a tamper-evident log cannot see: nothing in the log is wrong,
  because the change was never in the log.

Two ways to fail closed, both easy to get wrong:

- **An unknown event type is rejected, not skipped.** Skipping the events a
  reducer doesn't recognize silently forks state away from the log that is
  supposed to explain it — and the fork grows every time the schema changes.
- **An inapplicable event is rejected.** Resolving a finding that was never
  opened is not a no-op; it means the history and the state disagree.

Order is part of the state: the same multiset of events in a different
sequence produces a different digest, so "same events" never implies "same
state". Digests are taken over canonical JSON, so dict insertion order and
interpreter differences don't move them.

## Run it

```bash
cd apps/deterministic-ledger-replay
python -m unittest test_replay.py -v
```

All nine tests use a toy review-state machine (open/resolve a finding, assign
a reviewer): twice-replayed determinism, replay matching live state, order
sensitivity, key-order insensitivity, the empty ledger, an out-of-band write,
a tampered checkpoint, an unknown event type, and an inapplicable event.

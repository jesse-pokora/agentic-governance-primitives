# concurrent-append-integrity

**Atomic claim:** Under concurrent writers an append-only ledger admits
exactly one entry per accepted append, with contiguous indices and an unbroken
hash chain — a writer whose predecessor moved is rejected rather than silently
reordered or lost.

**Inspired by:** optimistic-concurrency append contracts in tamper-evident
logs (named for context; this app does not import or depend on any other
source). This is a v1.1 gap-closure app:
[execution-lock-and-recovery](../execution-lock-and-recovery) covers a crashed
run's lock, and nothing covered two live writers reaching the same ledger at
once.

**Enforcement class:** deterministic — the hazard is staged as an explicit
interleaving, and the racing tests assert an outcome that holds regardless of
scheduling.

## How it works

Three append paths on the same ledger, so the discipline is visible by
contrast rather than by assertion:

- **`append_unsafe(payload, prev_hash)`** — no coordination; the caller names
  its predecessor and is believed. Present only to demonstrate that the hazard
  is real. Two writers that both read the same head produce two entries with
  the same `prev_hash`, and `verify()` reports `chain_broken` at index 1.
- **`append_cas(payload, expected_head)`** — optimistic. The caller names the
  head it built on; if the head has moved, the append is rejected as
  `head_moved` and leaves no trace. Under a genuine eight-thread race where
  every thread reads the head before a `threading.Barrier` releases them,
  exactly one writer is accepted and seven are rejected.
- **`append_locked(payload)`** — pessimistic. The head is read and extended
  under one lock, so all eight writers succeed with indices `0..7`: no gaps,
  no duplicates, nothing lost.

`verify()` checks three things per entry — index contiguity, chain linkage,
and the recomputed entry hash — and names the first position that fails.
Contiguity matters on its own: a ledger whose entries are all individually
well-formed but whose indices skip has lost an append that something upstream
believes happened.

The two racing tests assert properties that are true under every possible
scheduling ("exactly one accepted", "all accepted with contiguous indices"),
not a particular interleaving, so they are not timing-dependent. They were run
40 times over while being written, with no failures.

## Run it

```bash
cd apps/concurrent-append-integrity
python -m unittest test_concurrent_ledger.py -v
```

All six tests use toy payloads and real threads (no simulated scheduler): the
uncoordinated hazard, a compare-and-swap rejection, the eight-thread CAS race,
eight serialized writers, a rejected append leaving nothing behind, and
non-contiguous index detection.

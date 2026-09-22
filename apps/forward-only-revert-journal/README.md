# forward-only-revert-journal

**Atomic claim:** A revert is recorded as a new forward record naming the state
it left behind — so the abandoned state is still readable afterwards, and a
history that was rewritten rather than appended to is detected.

**Inspired by:** append-only change history and compensating-record discipline
in auditable change systems (named for context; this app does not import or
depend on any other source). This is a v1.1 gap-closure app, split out of
[attested-rollback-checkpoint](../attested-rollback-checkpoint): *restore only
an attested digest* and *never erase history* are separable rules, and by this
catalog's one-sentence test they are two claims.

**Enforcement class:** deterministic — linkage equality across an append-only
record list, no heuristics.

## How it works

Every record names both the state in effect *after* it and the state in effect
*before* it (`from_digest`). `set_state(digest)` records a new state taking
effect; `revert_to(digest)` appends a `revert` record whose `from_digest` is
the state being abandoned.

Three properties follow:

- **Nothing is removed.** A revert is an append. The class exposes no method
  that deletes or edits a record, and after a revert the abandoned digest is
  still in `digests_that_held()`. A destructive revert deletes exactly the
  evidence an auditor came for — that the system was once in that state, and
  that someone decided to leave it.
- **A revert must name a state that previously held.** Reverting to something
  the system was never in is refused as `never_held`: it is a new state
  wearing the word *revert*, and should be recorded as one.
- **A rewritten history is detected.** `verify()` walks the records checking
  index contiguity and that each record's `from_digest` equals what was
  actually in effect before it. Deleting a record, reordering two, or editing
  one in place breaks that linkage at the point it was broken. This is the
  guard for something editing the list directly rather than going through the
  API.

Rolling "forward" again after a revert is not a special case — it is simply
another revert record, since the target previously held.

## Run it

```bash
cd apps/forward-only-revert-journal
python -m unittest test_revert_journal.py -v
```

All nine tests use toy digest strings (no real state or deployment): a revert
appending, the abandoned state surviving, a never-held target, an empty
journal, rolling forward, a clean verify, a deleted record, a record rewritten
in place, and the empty-journal verify.

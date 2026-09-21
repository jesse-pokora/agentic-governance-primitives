# trusted-revision-anchor

**Atomic claim:** The "current" commit is selected only from a ledger slot
position, never from caller-supplied input; "fresh" means "at the ledger
head," not "recent by clock time."

**Inspired by:** trusted revision/freshness contracts (named for context;
this app does not import or depend on that source).

**Enforcement class:** deterministic — `current()` and `is_fresh()` are
pure functions of ledger position, with no timestamp or caller-supplied
override anywhere in the API.

## How it works

`RevisionLedger.record(commit_id)` appends to an internal list and returns
its slot index — the only way a commit enters the ledger. `current()`
takes **no arguments**; it always returns `self._slots[-1]`, so there is no
call shape that lets a caller assert "trust this commit as current." A
test inspects `current()`'s signature directly to prove that structurally.

`is_fresh(commit_id)` answers "is this at the ledger head right now?" — a
pure position check, not a comparison against any clock or recorded
timestamp (none exists in this API).

## Run it

```bash
cd apps/trusted-revision-anchor
python -m unittest test_revision_ledger.py -v
```

Commit ids (`"commit-a"`, `"commit-b"`) are toy placeholders, not real
repository revisions.

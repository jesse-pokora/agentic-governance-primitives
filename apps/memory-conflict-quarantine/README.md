# memory-conflict-quarantine

**Atomic claim:** When two memory records assert different values for the same
key, both are retained and the conflict is surfaced — the newer one never
silently overwrites the older, and the key has no answer until someone
resolves it.

**Inspired by:** conflict-preserving replication and quarantine patterns in
distributed stores (named for context; this app does not import or depend on
any other source). Tier 5, v1.2.

**Enforcement class:** deterministic — exact value comparison per key.

## How it works

Last-write-wins is the default in nearly every store, and it is the wrong
default for agent memory. The newer record is not more trustworthy for being
newer — and a model that drifts writes its drift *last*. Under last-write-wins
the drift becomes the memory, and the record it replaced is gone.

`QuarantiningMemoryStore.write(record)` therefore has three outcomes:

- **New key** — settles.
- **Same value, any source** — settles. An identical re-assertion is
  corroboration, not a conflict.
- **Different value** — quarantined. Both the held and the incoming record are
  kept, each with its `source`, so the conflict is attributable to the runs
  that caused it.

`read(key)` on a conflicted key raises `key_in_conflict` rather than returning
either side. That is the load-bearing decision: returning *either* value would
be the silent choice the store exists to prevent, and returning the older one
is just last-write-wins with extra steps.

`resolve(key, chosen)` settles a conflict, and the chosen value must be one of
the values actually in conflict. Resolution is a decision *between what was
asserted* — not an opportunity to write a third value with no record of who
asserted it.

Conflicts are per key: a contradiction on one key leaves every other key
readable.

## Run it

```bash
cd apps/memory-conflict-quarantine
python -m unittest test_memory_store.py -v
```

All ten tests use toy memory records (no real agent memory): a first write, a
contradiction, a conflicted read, attribution of both sides, corroboration,
resolution, resolution with a never-asserted value, resolving a non-conflict,
an unknown key, and an unaffected neighbouring key.

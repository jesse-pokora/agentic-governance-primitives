# canonical-outcome-reconciliation

**Atomic claim:** Every input key in a batch receives exactly one
attributable success or failure outcome, in a fixed order — nothing
silently dropped, nothing double-counted.

**Inspired by:** ordered asset-reconciliation outcome contracts (named for
context; this app does not import or depend on that source).

**Enforcement class:** deterministic — outcome count, key set, and order
are asserted against the input batch on every call.

## How it works

`reconcile(batch)` takes an ordered `dict[str, Callable]`, calls each
action exactly once in insertion order, and appends exactly one `Outcome`
per key — `"success"` with the action's return value, or `"failure"` with
the exception's message if it raised. Before returning, it asserts the
outcome key sequence equals `list(batch.keys())` exactly, so a dropped or
duplicated key would fail loudly rather than silently.

Because Python `dict` preserves insertion order, "in a fixed order" falls
out of iterating the batch directly rather than needing a separate
ordering mechanism.

## Run it

```bash
cd apps/canonical-outcome-reconciliation
python -m unittest test_reconciliation.py -v
```

Batch keys (`"asset-1"`, `"good"`, `"bad"`) are toy placeholders standing
in for real reconciliation targets.

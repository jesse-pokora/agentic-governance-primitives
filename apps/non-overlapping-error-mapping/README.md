# non-overlapping-error-mapping

**Atomic claim:** Every test fixture reaches exactly one named validation
stage and exactly one named error — never two, never zero.

**Inspired by:** non-overlapping validation-stage error mapping (named for
context; this app does not import or depend on that source).

**Enforcement class:** deterministic — stage predicates are checked in a
fixed order with a guaranteed-matching terminal stage.

## How it works

`STAGES` is an ordered list of `(name, error_name, predicate)` triples,
ending in a catch-all `terminal` stage whose predicate always returns
`True`. `classify(fixture)` walks the list and returns the first matching
stage as an `Outcome(stage, error)`.

Short-circuiting on the first match guarantees **never two** (a fixture
that matches a later stage's predicate is never reached once an earlier
one has already matched). The catch-all terminal stage guarantees **never
zero** (every fixture matches something, even if it's just "valid, no
error").

One test goes further than relying on short-circuit order: it directly
checks each engineered fixture against every *earlier* stage's predicate
and asserts none of them also match — proving the mapping is genuinely
non-overlapping by construction, not just masked by evaluation order.

## Run it

```bash
cd apps/non-overlapping-error-mapping
python -m unittest test_validation.py -v
```

Fixtures (`{"id": ..., "amount": ...}`) are toy records, not real
transaction data.

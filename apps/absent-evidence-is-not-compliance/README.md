# absent-evidence-is-not-compliance

**Atomic claim:** A criterion whose checker exists but produced no evidence in
this run is recorded as `not_observed` — never as passed, and never dropped
from the report.

**Inspired by:** the NOT-OBSERVED status in instruction-adherence evidence
registries (named for context; this app does not import or depend on any other
source). Tier 2, v1.5.

**Enforcement class:** deterministic — one row per declared criterion.

## How it differs from the app next to it

[instruction-policy-gate](../instruction-policy-gate) covers the case where
**no checker exists**: the policy is incomplete. This covers the case where the
checker exists and the **run** didn't exercise it.

They fail the same way if you let them — a report saying nothing failed,
because the things that would have failed were never looked at — but they are
fixed differently. One needs a checker written; the other needs the run
extended.

## How it works

`RunLedger.record(criterion, status, evidence)` accepts `passed` or `failed`,
and **both require evidence**. An assertion with nothing behind it is
indistinguishable from not looking, right up until somebody asks what the
evidence was.

`not_observed` cannot be recorded deliberately. It is what `report()` produces
for a declared criterion with no observation — the absence of a record, not a
record. Letting a run write it would let a criterion be marked unlooked-at on
purpose, which is worse than the gap it describes.

`clean()` is deliberately not "nothing failed". It is true only when every
declared criterion was observed *and* passed. A run that looked at two of ten
and found no failures is not a clean run, and `observed()` returns *(2, 10)* so
that is visible.

`merge()` combines runs: coverage accumulates, and two runs that disagree about
the same criterion are **refused rather than resolved**. Picking a winner
silently is how a flaky failure becomes a pass.

## Run it

```bash
cd apps/absent-evidence-is-not-compliance
python -m unittest test_observation.py -v
```

Twelve tests over toy criterion ids: unobserved criteria surfacing, nothing
dropped, "nothing failed" not being clean, a fully observed run, a failure,
evidence required, `not_observed` refused as an input, an undeclared criterion,
a double observation, merging coverage, merging a disagreement, and merging
different declarations.

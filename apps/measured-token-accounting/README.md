# measured-token-accounting

**Atomic claim:** An unmeasured model call is refused rather than counted as
zero, and the recorded per-call parts must reconcile exactly with the
provider's own reported total.

**Inspired by:** usage metering and reconciliation contracts in metered
systems (named for context; this app does not import or depend on any other
source). Tier 5, v1.2.

**Enforcement class:** deterministic — integer arithmetic and exact equality,
no estimation and no tokenizer of its own.

## How it works

The app is built around one distinction: **`None` is not `0`.**

A call that genuinely consumed nothing is a measurement, and is recorded. A
call whose usage never arrived is *unknown*, and `record(call_id, None)` is
refused as `unmeasured_call`. Treating unknown as zero is how a budget drifts
away from reality while continuing to look balanced — every number in the
ledger is defensible and the total is still wrong.

Deliberately, this app does **not** count tokens itself. A hand-rolled
tokenizer would be a guess dressed as a measurement, and the two would diverge
silently as models change. Usage comes from the provider; this app's job is
that the accounting around it is honest:

- **No double counting.** A repeated `call_id` is refused as `duplicate_call`
  — the other direction a total can drift.
- **No negative usage.** Refused as `invalid_usage`.
- **Reconciliation.** `reconcile(provider_reported_total)` requires the sum of
  the parts to equal the whole the provider reports. A mismatch means a call
  happened that this account never saw, which is exactly the failure a
  per-call ledger exists to make visible — and exactly what a single running
  counter cannot detect.

Pairs with [bounded-execution-budget](../bounded-execution-budget): that app
enforces the cap, this one establishes that the number being capped is real.

## Run it

```bash
cd apps/measured-token-accounting
python -m unittest test_token_account.py -v
```

All nine tests use toy usage figures (no provider call): summing, an
unmeasured call, a genuine zero-token call, a duplicate, negative usage, an
empty id, a clean reconciliation, a missed call surfacing as a mismatch, and
the empty account.

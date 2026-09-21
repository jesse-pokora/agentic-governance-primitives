# bounded-review-epoch-escalation

**Atomic claim:** After 3 review rounds with open findings, the loop stops
and requires a *new*, hash-bound human reauthorization naming the exact
terminal evidence — it cannot self-extend.

**Inspired by:** hard-capped review-epoch escalation policies (named for
context; this app does not import or depend on that source).

**Enforcement class:** deterministic — the round cap and the hash equality
check on reauthorization are both binary pass/fail.

## How it works

`BoundedReviewEpoch.submit_round(open_findings)` records a round. If
findings are empty, the epoch closes. If the round count since the last
reauthorization reaches `max_rounds_per_epoch` (default 3) and findings are
still open, the epoch computes a SHA-256 hash over the terminal round's
evidence (round number + open findings) and returns
`status="escalation_required"` — every subsequent `submit_round` call raises
`EscalationRequired` until a human calls `reauthorize(evidence_hash)` with
that *exact* hash.

There is no code path inside `BoundedReviewEpoch` that clears the
escalation on its own — only an external caller supplying the exact
terminal-evidence hash can. A successful reauthorization unlocks exactly one
further epoch of up to `max_rounds_per_epoch` rounds; if findings are still
open at the end of that epoch, it escalates again with a **new** hash — the
old one no longer works.

## Run it

```bash
cd apps/bounded-review-epoch-escalation
python -m unittest test_review_loop.py -v
```

Findings (`"finding A"`, `"missing null check"`) are toy placeholders
standing in for real review output.

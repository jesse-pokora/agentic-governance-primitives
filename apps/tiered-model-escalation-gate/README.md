# tiered-model-escalation-gate

**Atomic claim:** A cheap tier's output is used only if it passes the declared
deterministic check — otherwise the call escalates to the next tier, and the
ledger records which tier actually answered.

**Inspired by:** model-routing and escalation patterns in cost-tiered
inference (named for context; this app does not import or depend on any other
source). Tier 5, v1.2.

**Enforcement class:** hybrid — a deterministic envelope around generated
content, in the same sense as
[single-purpose-adversarial-reviewer](../single-purpose-adversarial-reviewer).

## How it works

`TieredEscalationGate(tiers, check)` takes tiers in declared order and one
deterministic `check`. `answer(prompt)` walks the tiers and returns the first
output that passes.

The point is not that cheap models are bad. It is that **"we asked the cheap
one first" must never be a reason output reaches a caller unchecked.** Three
properties carry that:

- **Cost does not buy trust.** Every tier faces the same check. A strong
  tier's failing output is rejected exactly as a cheap one's is — there is no
  path by which unchecked output reaches the caller, and no "it came from the
  expensive model" exemption.
- **A broken tier does not take the call down.** A tier that raises is
  recorded as a failed attempt and escalated past. A cheap tier having a bad
  day should cost latency, not availability.
- **The ledger records who answered.** Each `Answer` carries `answered_by` and
  the full attempt list, so "how often does the cheap tier actually hold up"
  is a query against recorded fact rather than an assumption. That number is
  the one that tells you whether the tiering is earning anything.

When no tier passes, `NoTierPassed` carries every attempt and **nothing is
written to the ledger** — the gate has no degraded mode that returns the least
bad failing output.

The `check` is supplied by the caller; in the tests it is a grounding check,
which is the natural pairing with
[grounded-claim-verification](../grounded-claim-verification).

## Run it

```bash
cd apps/tiered-model-escalation-gate
python -m unittest test_escalation_gate.py -v
```

All seven tests use toy spy tiers that count their own invocations (no model
call): a passing cheap tier, escalation, the ledger, total failure, a raising
tier, the expensive tier facing the same check, and the empty-tier-list guard.

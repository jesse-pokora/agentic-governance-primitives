# exact-plan-approval-gate

**Atomic claim:** A destructive action can only be approved by echoing back
the *exact* SHA-256 of the plan that was shown — a "yes" with no hash is
rejected.

**Inspired by:** prepare/approve/execute governed-evaluation contracts
(named for context; this app does not import or depend on that source).

**Enforcement class:** deterministic — the provided value either equals the
current plan's SHA-256 hex digest or it doesn't.

## How it works

`show_plan(plan_text)` returns a `ShownPlan` carrying the plan text and its
SHA-256 hash — what a human would see before approving. `approve_and_execute
(current_plan_text, provided_value)` executes only if `provided_value`
equals `plan_hash(current_plan_text)` exactly. Everything else — a bare
`"yes"`, an empty string, a wrong hash, or the hash of a plan that has since
been edited — raises `ApprovalDenied`.

Recomputing the hash from the *current* plan text (not trusting a
previously cached hash) is what catches a plan that was shown, approved, and
then silently mutated before execution.

## Run it

```bash
cd apps/exact-plan-approval-gate
python -m unittest test_approval_gate.py -v
```

The plan text is a toy fake SQL statement — no real data or destructive
command is ever run.

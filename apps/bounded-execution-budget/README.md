# bounded-execution-budget

**Atomic claim:** A run halts at the first action that would exceed a declared
budget — the over-budget action never executes, nothing is partially charged,
and the budget cannot be extended from inside the run.

**Inspired by:** resource-bounded execution contracts in governed agent
runtimes (named for context; this app does not import or depend on any other
source). This is a v1.1 gap-closure app:
[bounded-review-epoch-escalation](../bounded-review-epoch-escalation) hard-caps
one specific loop, and nothing capped a run's consumption of tool calls,
cost, or time.

**Enforcement class:** deterministic — integer comparison against a frozen
limit, with an injected clock so the time bound is exact rather than
machine-speed dependent.

## How it works

`BoundedExecutionBudget(limits)` declares every resource up front and copies
the limits. There is no method that raises a limit, so a run cannot extend its
own budget; an undeclared resource is denied as `unknown_resource` rather than
treated as unlimited, because a new cost that nobody declared is exactly the
cost that should not be invisible.

`run(Charge(resource, amount), action, ...)` checks before it charges and
charges before it runs:

- **Countable resources are precharged.** Tool calls, cost units, and tokens
  have a cost known in advance, so the comparison happens before the action.
  An action that would cross the cap is refused whole — `spent` is unchanged
  after a denial, so the meter still reads what the run actually consumed.
- **Wall-clock is bounded by a deadline, not a precharge.** An action's
  duration is not knowable in advance, so time cannot honestly be precharged.
  Instead an action is refused if the clock has already passed the deadline
  when it would start. The clock is injected, so the test asserts exact tick
  values instead of sleeping.
- **Denial halts the run.** After any denial the budget is terminal: a later,
  affordable charge against a different resource is refused as `run_halted`.
  A meter that keeps serving whatever still fits lets a run route around its
  own cap.
- **A failing action is still charged.** The charge lands before the call, so
  a tool that raises has still consumed the resource it consumed. Refunding it
  would let a run retry for free.

## Run it

```bash
cd apps/bounded-execution-budget
python -m unittest test_budget.py -v
```

All nine tests use a toy spy action and a fake clock (no real tool, model
call, or spend): staying inside the budget, crossing the cap, an oversized
single action, the halt being sticky, an undeclared resource, a non-positive
charge, the deadline, a failing action's charge, and post-construction
mutation of the limits.

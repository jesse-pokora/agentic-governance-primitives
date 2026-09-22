# provable-dry-run

**Atomic claim:** A dry run performs no effect and still produces the complete
plan — and the plan a dry run produces is the same plan the live run produces,
because both execute the same routine.

**Inspired by:** dry-run guarantees in governed write paths (named for
context; this app does not import or depend on any other source). Tier 2,
v1.3.

**Enforcement class:** deterministic — one gate, one branch.

## How it works

The usual dry-run bug is a conditional at every call site: `if not dry_run:
write(...)`. Miss one and the mode is silently broken, and the miss stays
invisible until the day it writes something.

Here every effect goes through one `Executor.perform(effect, action)`. The
intent is recorded in both modes; the action is invoked only when live. "Did
we honour dry run" becomes a property of one function instead of a property of
everyone's discipline.

The load-bearing test is `test_the_dry_plan_equals_the_live_plan`. The demo
routine has **no dry-run branch inside it** — both modes call the same code —
so the plan a dry run prints is the live run's intent, rather than a separate
code path that happens to print something similar. A dry run you cannot trust
to describe the real run is worse than no dry run, because it is reassuring.

`planned` and `performed` are tracked separately, so the divergence is
inspectable: in dry mode `planned` fills and `performed` stays empty; in live
mode they are equal.

## What this does not prove

Stated as a test, not just prose: `test_an_effect_that_bypasses_the_gate_is
_invisible_to_the_plan` writes a file directly and shows the executor neither
knows nor reports it. This app proves that effects **routed through the gate**
are suppressed. It cannot prove that nothing else in a codebase writes
directly — that is a property of the codebase, enforced by review or by making
the gate the only thing holding a writable handle.

## Run it

```bash
cd apps/provable-dry-run
python -m unittest test_dry_run.py -v
```

All eight tests use real temp files: a dry run writing nothing, a dry run
producing a full plan, a live run performing, the two plans matching, an
existing file untouched, planned/performed divergence, an unattributed effect
refused in both modes, and the bypass limitation.

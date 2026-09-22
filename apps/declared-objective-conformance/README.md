# declared-objective-conformance

**Atomic claim:** Every action must cite an objective declared for the run — an
action citing nothing, or citing an objective never declared, is refused before
it executes, and the declared set cannot be widened from inside the run.

**Inspired by:** goal-conformance checks for autonomous agents (named for
context; this app does not import or depend on any other source). Tier 5,
v1.4. Strengthens ASI10 coverage in [CONFORMANCE.md](../../CONFORMANCE.md).

**Enforcement class:** deterministic — set membership against a frozen
declaration.

## How it works

This is goal drift made checkable. An agent does not usually go off-mission by
announcing it. It takes one reasonable-looking action that serves a purpose
nobody asked for, then another, and the log reads as a sequence of sensible
decisions. Requiring each action to **name the objective it serves** turns that
into a refusal instead of a surprise.

`Run.declaring({...})` freezes the objectives. `perform(action, do)` refuses
two ways before calling anything:

- **`uncited_action`** — the action names no objective at all.
- **`undeclared_objective`** — it names one that was never declared. Every
  undeclared objective is listed, not just the first: an action citing two of
  them has drifted twice and both are worth seeing.

One undeclared objective taints an otherwise valid action. An action serving
`summarize-repository` *and* `ship-it` is refused, because the second is the
part nobody authorized and it would happen anyway.

The declared set is copied into a frozenset at declaration, so mutating the set
you passed in grants nothing — the same runtime-escalation shape that
[capability-gated-tool-invocation](../capability-gated-tool-invocation) refuses,
applied to objectives instead of capabilities.

**A declared objective that nothing served is not a violation.** A run may
find an objective needs no action, and `objectives_served()` exists so that can
be asked rather than assumed.

## What this does not do

It checks that an action *claims* a declared objective, not that the action
genuinely advances it. A dishonest citation passes. That limit is inherent —
whether an action truly serves a goal is a judgment, and this catalog's
deterministic apps do not make judgments. What it buys is that drift has to be
accompanied by a false statement on the record, which is a much smaller place
to hide than silence.

## Run it

```bash
cd apps/declared-objective-conformance
python -m unittest test_objectives.py -v
```

All eleven tests use toy objectives and actions: a cited action, an uncited
one, an undeclared objective, one undeclared among valid ones, several
undeclared named at once, multiple declared objectives, widening the source set
after declaring, immutability, an empty declaration, an unserved objective, and
only performed actions being recorded.

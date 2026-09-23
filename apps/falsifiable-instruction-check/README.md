# falsifiable-instruction-check

**Atomic claim:** An instruction registers only if its own checker rejects the
violating fixture it ships and accepts the satisfying one — a checker that
cannot discriminate between them is refused.

**Inspired by:** the unit layer of instruction-adherence test architectures,
which requires a detector to recognize positive *and* negative fixtures (named
for context; this app does not import or depend on any other source). Tier 2,
v1.5.

**Enforcement class:** deterministic — the checker is run against both fixtures
at registration.

## Why a checker has to prove it can fail

A policy full of checkers that never fire reports total compliance and means
nothing. It is also the easiest thing in this whole catalog to build by
accident: a checker with a subtly wrong pattern passes every artifact, forever,
silently, and looks exactly like a checker that is working.

There is a test for precisely that shape — a checker looking for `evaluate(`
when the instruction forbids `eval(`. It reads correctly, it matches nothing,
and registration refuses it.

## How it works

`register(candidate)` runs the candidate's own checker against the two fixtures
it ships and refuses five ways:

- **`checker_accepts_violation`** — vacuous. It passes an artifact it exists to
  reject.
- **`checker_rejects_satisfying`** — the other useless direction. It fails
  everything, and will be switched off within a day.
- **`missing_violating_fixture`** / **`missing_satisfying_fixture`** — without
  both, there is no way to tell a strict checker from a stub.
- **`checker_errored`** — naming which fixture broke it.

The fixtures stay attached to the registered instruction, so the evidence that
this checker *can* fail travels with it and can be re-verified later rather
than taken on trust.

## Run it

```bash
cd apps/falsifiable-instruction-check
python -m unittest test_falsifiable.py -v
```

Ten tests over a toy "must not call eval()" instruction: a sound checker, one
that accepts everything, one that rejects everything, the subtly wrong pattern,
both missing fixtures, a raising checker, fixtures staying attached, a registry
admitting only falsifiable instructions, and a duplicate id.

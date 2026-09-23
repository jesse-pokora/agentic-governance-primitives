# composition-root-construction

**Atomic claim:** A declared collaborator type may be constructed only inside
the composition root; anywhere else it must arrive as a parameter.

**Inspired by:** architectural instructions in always-on agent instruction
files (named for context; this app does not import or depend on any other
source). Tier 1, v1.5.

**Enforcement class:** deterministic — AST inspection with exact name matching.

## Making "use dependency injection" checkable

"Always use dependency injection and inversion of control" is not a checkable
instruction. It names a style, and a style cannot be a gate.

"These types are constructed in exactly these functions" *is* checkable — and
it is what the style is actually for: one place that knows how the system is
wired, everywhere else taking what it is given. Turning the instruction into
that sentence is most of the work; the AST walk is the easy part.

## What counts as a collaborator is declared, not guessed

`Policy.of(collaborators, composition_root)` names both. A checker that decided
for itself which calls look like collaborators would flag `Decimal("1.00")` and
be switched off by lunchtime — so the policy says which types must be injected,
and everything else is left alone. There is a test where a class constructs a
list and a `Decimal` and comes back `not_applicable`.

A policy with no composition root is refused: the rule would become "never
construct these", which is unsatisfiable.

## The four shapes it catches

- **In `__init__`** — the textbook violation.
- **In any other method** — the same violation, later.
- **At module level** — the sneakiest. The class looks injected and the wiring
  has just moved one line out of sight.
- **In a default argument** — `def handler(repo=SqlRepository())`.

A *mention* is not a construction: a type annotation or an `isinstance` check
passes. And `not_applicable` is distinct from `passed`, for the reason
[instruction-policy-gate](../instruction-policy-gate) exists — source with no
collaborator in it has not satisfied the instruction, there was just nothing to
satisfy.

Every offending site is reported, not the first, so one pass over the file
gives the whole list.

## Run it

```bash
cd apps/composition-root-construction
python -m unittest test_composition.py -v
```

Twelve tests over toy modules: wiring in the root, construction in `__init__`,
in another method, at module level, in a default argument, an undeclared type,
source that never mentions one, a mention without construction, several sites
reported, unparseable source, and both policy refusals.

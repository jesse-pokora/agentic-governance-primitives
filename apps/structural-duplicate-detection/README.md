# structural-duplicate-detection

**Atomic claim:** Two functions with the same implementation shape produce the
same fingerprint regardless of their names, so a re-implementation under a new
name is detected exactly.

**Inspired by:** duplicate-effort detection in agent-written code (named for
context; this app does not import or depend on any other source). Tier 5,
v1.5.

**Enforcement class:** deterministic — alpha-normalized AST, hashed. No
similarity score, no threshold.

## The failure it is aimed at

An agent forgets a dependency it already has and writes the function that
already exists, under a name it invented. Nothing notices, because nothing was
looking for the *shape* — and the name is the one part guaranteed to differ.

So the fingerprint discards names. Parameters and locals are renamed to
positional slots in order of first appearance, docstrings are dropped, and what
remains is hashed. `normalize_path(raw)` and `tidy_path_value(value)` with the
same body produce the same fingerprint, and there is a test that is exactly
that pair.

## What is kept, and why

**Literals and operators are kept.** Two functions differing only in a constant
are doing different things, and collapsing them would make the fingerprint lie
— `x + 1` and `x + 2` are not duplicates. So is calling a different helper:
`clean(x)` and `scrub(x)` are different implementations, so only names *bound
inside* the function are normalized away.

## What this cannot do

A genuinely different implementation of the same idea produces a different
fingerprint and **is not reported**. That is not an oversight, it is the
boundary: catching it needs similarity scoring, which needs a threshold, which
is a number somebody picks — and a picked number is not deterministic however
carefully it is chosen.

The governance answer to that case is not better detection. It is making the
existing capability declared and discoverable, so the duplicate is refused when
it is declared rather than found afterwards.

## Run it

```bash
cd apps/structural-duplicate-detection
python -m unittest test_fingerprint.py -v
```

Fourteen tests: the renamed re-implementation, a genuinely different one,
renamed parameters, an added docstring, a changed literal, a changed operator,
a different helper, grouping across two modules, a function with no twin,
duplicates within one module, nested functions, report stability, unparseable
source, and comparing nothing.

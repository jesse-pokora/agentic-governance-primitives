# enforcement-mechanism-attribution

**Atomic claim:** A result that does not name the mechanism enforcing an
instruction cannot be compared with one that does.

**Inspired by:** the mechanism layer of instruction-adherence test
architectures (named for context; this app does not import or depend on any
other source). Tier 3, v1.5.

**Enforcement class:** deterministic — the mechanism vocabulary is closed and
ordered.

## Why the mechanism belongs in the record

The same instruction delivered as prose, as a skill, as a hook, as a gate, or
by the host produces different adherence. A result that omits which one was in
effect is not a data point about the instruction — it is a data point about an
unknown.

That is the difference between "the instruction works" and "the instruction
works when a gate enforces it". Only the second tells you what to build, and
only the second survives somebody moving it from a prompt into a linter.

## How it works

`MECHANISMS` runs weakest to strongest by how much the agent has to cooperate:
`prose`, `skill`, `hook`, `gate`, `host`. `compare(first, second)` orders the
two results by that scale regardless of argument order and returns one of:

- **`stronger_mechanism_helped`** — the weaker one was ignored, the stronger
  one held. The instruction needs enforcement, not wording.
- **`weaker_sufficed`** — followed under prose alone. A gate would be cost
  without benefit.
- **`no_difference`** — ignored under both. Neither the wording nor the
  enforcement is the problem.

Three refusals: an unrecorded mechanism, the same mechanism on both sides
(that compares runs, not mechanisms), and results about different instructions.

`None` is accepted as a mechanism and is not the same as a missing field: it
records that nobody wrote down what was in effect, which is a fact — and it is
exactly the fact that makes the comparison refuse later.

## Run it

```bash
cd apps/enforcement-mechanism-attribution
python -m unittest test_mechanism.py -v
```

Ten tests over toy results: a gate rescuing adherence, prose sufficing, no
difference, an unrecorded mechanism, recording an unknown deliberately, the
same mechanism twice, different instructions, a mechanism outside the
vocabulary, ordering independent of argument order, and the scale itself.

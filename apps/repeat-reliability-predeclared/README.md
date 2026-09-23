# repeat-reliability-predeclared

**Atomic claim:** The number of attempts is declared before the first one runs,
every attempt is retained, and a conclusion drawn from fewer than the declared
number is refused.

**Inspired by:** predeclared run counts for repeat-reliability claims (named
for context; this app does not import or depend on any other source). Tier 2,
v1.5.

**Enforcement class:** deterministic — integer comparison against a frozen
plan.

## The failure this closes is drift, not fraud

Run it again because that one looked odd. Run it once more to be sure. Stop
when it is green. Every step is reasonable and the series that results measures
the stopping rule rather than the system.

Declaring the count first turns stopping early into a refusal instead of a
judgment call — which is the only version of this that survives a deadline.

## How it works

`Plan(runs, configuration)` is frozen at construction and a single run is
refused: one attempt cannot disagree with anything, so it says nothing about
repeat reliability. `Series.record` retains every attempt; nothing is
overwritten or discarded.

`conclude()` refuses while the series is short, and otherwise reports:

- **`stable`** — every attempt agreed. Note that a series of five failures is
  stable: stable means the system agrees with itself, not that the news is
  good.
- **the distribution**, never a majority. An unstable series has `outcome =
  None`, because reporting the majority would turn "this fails one time in
  five" into "this passes" — the whole failure this app exists to prevent.

Extra attempts beyond the declared count are **included**, not trimmed.
Discarding them would be the same selective stopping running backwards.

## Run it

```bash
cd apps/repeat-reliability-predeclared
python -m unittest test_repeats.py -v
```

Ten tests over toy outcomes: a completed stable series, stopping at four of
five, an unstable series with no outcome, the distribution, every attempt
retained, an extra attempt included, a frozen plan, a single declared run, an
empty outcome, and a stable series of failures.

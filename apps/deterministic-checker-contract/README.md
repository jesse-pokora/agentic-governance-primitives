# deterministic-checker-contract

**Atomic claim:** A checker must return the same verdict for the same artifact
on repeated evaluation — one that does not is refused, and the refusal reports
the whole distribution.

**Inspired by:** repeat-reliability requirements for graded and model-dependent
claims (named for context; this app does not import or depend on any other
source). Tier 2, v1.5.

**Enforcement class:** deterministic — verdicts are compared for equality.

## Why a flaky checker is worse than no checker

Its failures arrive at random, so a red result gets re-run until it goes green
and nobody learns anything. The instruction it guards ends up enforced on
whichever attempts happened to agree with it, and the suite reports a number
that measures the retry policy.

This sits next to
[falsifiable-instruction-check](../falsifiable-instruction-check) and answers a
different question. That one asks whether a checker *can* fail; this one asks
whether it fails *consistently*. A checker can be falsifiable and flaky, or
deterministic and vacuous.

## How it works

`evaluate_repeatedly(check, artifact, runs=3)` runs the checker several times
on the same artifact and returns the verdict only if every run agrees.

- **One run is refused.** A single evaluation cannot disagree with anything, so
  it can never detect the condition this function exists to detect.
- **The refusal reports the distribution**, not the fact of disagreement.
  "Sometimes fails" is not actionable; `passedx3, failedx2` is.
- **Different verdicts for different artifacts are the point.** `certify` walks
  a list, and only disagreement about the *same* artifact is a defect.

The tests cover the three ways a checker usually acquires state without anyone
intending it: counting its own calls, consulting a clock, and being run fewer
times than would reveal either.

## Run it

```bash
cd apps/deterministic-checker-contract
python -m unittest test_determinism.py -v
```

Ten tests over toy source strings: a pure checker, a call-counting one, the
distribution in the message, a clock-dependent one, a single run, a raising
checker, different artifacts, certification stopping at the first bad one, an
empty list, and a stable verdict over twenty-five runs.

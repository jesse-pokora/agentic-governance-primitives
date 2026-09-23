# ablation-required-for-causal-claim

**Atomic claim:** A finding may be recorded as *caused by* an instruction only
when a leave-one-out comparison exists — two runs identical in every declared
factor except that instruction. Without one it is recorded as a correlation.

**Inspired by:** the ablation layer of instruction-adherence test architectures
(named for context; this app does not import or depend on any other source).
Tier 2, v1.5.

**Enforcement class:** deterministic — factor sets are compared for equality.

## The default diagnosis is the dangerous one

An agent produced a bad outcome and an instruction was violated, so the
violation caused the outcome. It is the conclusion everybody reaches and almost
nobody tests, and on the strength of that coincidence the instruction earns
permanent residency in a prompt that every future run pays for.

There is a test named for that shape: a violation alongside a poor outcome
still comes back `correlated`, never `caused`.

## How it works

`attribute(instruction_id, treatment, control)` returns a `Finding` whose
`relation` is as strong as the evidence allows:

- **`correlated`** — no control run. The finding is *recorded*, not discarded:
  an observed omission is worth knowing, it just is not a cause.
- **`caused`** — a control exists, differs only by this instruction, and the
  outcomes differ.
- **`no_effect`** — a clean comparison where the outcome was the same either
  way. This is the result that retires an instruction, and it is the one
  nobody goes looking for.

Three ways a comparison is refused outright rather than downgraded:

- **`confounded_comparison`** — some other factor changed too, and the denial
  names which. If the model version moved between runs, the comparison cannot
  say which difference did the work.
- **`multiple_instructions_removed`** — the control dropped more than one, so
  the effect cannot be assigned to either.
- **`control_retains_instruction`** — it is not an ablation.

## Run it

```bash
cd apps/ablation-required-for-causal-claim
python -m unittest test_attribution.py -v
```

Ten tests over toy runs: no control, a correlation being recorded, a clean
ablation, no effect, a changed model, several confounds named, two instructions
removed at once, a control that kept the instruction, an instruction that was
never in effect, and the default-diagnosis case.

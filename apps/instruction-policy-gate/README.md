# instruction-policy-gate

**Atomic claim:** Every declared instruction receives an explicit verdict from
a fixed vocabulary — and an instruction with no mechanical checker is reported
as `unenforceable`, never counted as satisfied.

**Inspired by:** instruction-adherence criteria records (named for context;
this app does not import or depend on any other source). Tier 2, v1.5.

**Enforcement class:** deterministic — the verdict vocabulary is closed and
the report has one row per declared instruction.

## The failure this prevents

A compliance report that lists only the instructions somebody wrote a checker
for reads as full marks. The instructions nobody could check are exactly the
ones worth knowing about, and leaving them out is how a policy that verifies a
third of itself reports as green.

So the report always has one row per declared instruction, and the vocabulary
has four values:

| Verdict | Meaning |
|---|---|
| `passed` | A checker ran and the artifact satisfies the instruction. |
| `failed` | A checker ran and the artifact violates it. |
| `not_applicable` | A checker ran and found nothing the instruction could apply to. |
| `unenforceable` | No mechanical checker exists. Nobody has verified this. |

`not_applicable` and `passed` are deliberately different. An instruction about
module-level singletons, checked against an artifact with no module-level
assignments, has not been satisfied — there was simply nothing for it to be
satisfied by. Collapsing the two inflates every compliance percentage in the
report.

## Two properties worth the tests they have

- **`unenforceable` is not a verdict a checker can return.** It is what the
  *absence* of a checker produces. If a checker could return it, an instruction
  could mark itself unverifiable and disappear from the part of the report
  anyone reads.
- **Coverage is reported separately from admission.** `report.coverage()`
  returns *(checked, declared)* — so 2 of 3 is visible even when nothing
  failed. "Nothing failed" and "everything was verified" are different
  statements, and only one of them is usually true.

An unenforceable instruction does not block admission: it is not evidence of a
violation. It is not evidence of compliance either, and coverage is where that
shows.

A checker that raises invalidates the whole report rather than marking one
instruction failed. A broken checker means the report is not trustworthy, and
a report that is wrong in an unknown place is worse than no report.

## Run it

```bash
cd apps/instruction-policy-gate
python -m unittest test_policy_gate.py -v
```

All twelve tests use toy instructions and stub checkers: one row per
instruction, an unenforceable instruction, a checker trying to return
`unenforceable`, coverage, `not_applicable` versus `passed`, a failure blocking
admission, an unenforceable instruction not blocking, an invented verdict, a
raising checker, duplicate ids, an empty policy, and an instruction with no id.

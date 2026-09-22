# grounded-claim-verification

**Atomic claim:** Every factual claim a model emits must name a ground-truth
key that exists and quote that record's value exactly — an uncited claim, an
invented source, or an altered quote fails closed.

**Inspired by:** citation-grounding and attribution checks for generated text
(named for context; this app does not import or depend on any other source).
Tier 5, v1.2.

**Enforcement class:** deterministic — string equality against held records.
No semantic judgment, no model in the loop, no second model grading the first.

## How it works

The model is required to emit claims in a structured form —
`Claim(text, source_key, quoted_value)` — and `verify_claims` checks three
things per claim, in a fixed order:

1. **Cited at all.** A claim with no `source_key` is `uncited_claim`.
2. **The source exists.** A `source_key` not in the ground truth is
   `unknown_source`. This is the most convincing drift, because it *looks*
   cited — a citation check that only asks "is there a citation?" passes it.
3. **The quote matches.** The `quoted_value` must equal the held record
   exactly, or it is `quote_mismatch`. Right key, drifted value is the failure
   the first two checks miss entirely, and it is the characteristic shape of a
   cheaper or degraded model: the structure survives, the content slips.

**What this app does not do:** it does not judge whether a claim is *true*. It
checks whether the claim is anchored to a record the system actually holds and
whether the value attributed to that record is the value it contains. That is
a smaller question, and it is the part that can be answered deterministically
— which is the whole reason it makes a usable gate.

Quote comparison is exact. Normalizing whitespace or case would be a policy
decision about how much drift is acceptable, and this app deliberately does
not make it: an exact gate can be loosened on purpose, while a fuzzy one can
never be tightened back with confidence.

## Run it

```bash
cd apps/grounded-claim-verification
python -m unittest test_grounding.py -v
```

All eight tests use a toy ground-truth set (no model call and no retrieval):
grounded claims, an uncited claim, a fabricated source key, an altered quote,
three near-miss quotes, a missing quote, first-bad-claim ordering, and the
vacuous empty case.

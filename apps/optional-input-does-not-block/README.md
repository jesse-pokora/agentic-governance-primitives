# optional-input-does-not-block

**Atomic claim:** A run starts when every required input is present, even if
every optional one is missing — a missing optional input is recorded and the
run marked degraded, never escalated into a stop.

**Inspired by:** direct-intake sufficiency rules in governed agent contracts
(named for context; this app does not import or depend on any other source).
Tier 2, v1.3.

**Enforcement class:** deterministic — presence checks against a declared
spec.

## Why this app exists

Every other app in this catalog teaches fail-closed. A system built only from
those refuses to start over context it never needed, and the result is an
agent that is perfectly governed and unusable.

Knowing what *not* to block on is the other half of the craft, and it is
harder, because the failure is invisible in review. Nobody files a bug saying
"this refused correctly but should not have." They just stop using it.

## How it works

`evaluate_startup(specs, supplied)` classifies each declared input as required
or optional, and:

- **Refuses only on missing required inputs**, reporting *all* of them at once.
  The other apps here report the first violation, because they are answering
  "is this safe"; this one is answering "what do you need from me", and a
  caller fixing intake should learn the whole list in one round.
- **Starts degraded when optional inputs are absent**, recording exactly which
  ones. A bare prompt with no run ID, no commit, no evidence packet and no
  approval record is sufficient intake.
- **Treats present-but-empty as missing** for required inputs — `""`, `None`,
  `[]` and `{}` are missing wearing a costume, and accepting them is how a
  required input quietly becomes optional.
- **Accepts whitespace-only as present.** Emptiness is length, not meaning;
  stripping would make the gate's answer depend on a judgment about content.
- **Treats an undeclared field as context, not a violation.**

That last one is worth sitting with, because it looks like a contradiction.
[single-purpose-adversarial-reviewer](../single-purpose-adversarial-reviewer)
rejects unexpected fields, and it is right to. The difference is what a
mistake costs on each side. In a closed output schema, an unexpected field may
be an instruction the caller expects to be honoured, and ignoring it is a
silent divergence. At intake, an unexpected field is something nobody will
read, and refusing it costs a run that could have succeeded. Strictness
belongs where the extra data would otherwise be acted on.

## Run it

```bash
cd apps/optional-input-does-not-block
python -m unittest test_startup.py -v
```

All nine tests use toy intake envelopes: a full envelope, a bare prompt, a
partially degraded start, a missing required input, several missing at once,
present-but-empty values, whitespace-only, an undeclared field, and an empty
optional not being carried into the run.

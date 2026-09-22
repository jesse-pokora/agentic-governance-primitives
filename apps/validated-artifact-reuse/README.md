# validated-artifact-reuse

**Atomic claim:** An existing artifact is reused only when it is still valid
for the inputs at hand — same input digest and same producer version — and
every decision records which way it went and why.

**Inspired by:** upstream-artifact reuse contracts in governed agent runs
(named for context; this app does not import or depend on any other source).
Tier 2, v1.3.

**Enforcement class:** deterministic — SHA-256 equality over canonical JSON.

## How it works

Reuse and cache invalidation are the same problem wearing different words, and
the failure that matters is not a slow rebuild. It is a **fast, confident
answer computed from inputs that have since changed** — indistinguishable from
a correct one until somebody checks.

So `obtain(existing, inputs, producer_version, produce)` makes the decision
explicit and returns it: `reused`, a `reason` from a fixed vocabulary, and the
artifact. Every call reports which way it went, so "how often are we actually
reusing" is a query rather than an assumption.

**Validity is checked against what the artifact was made from, never against
when it was made.** A clock-based expiry answers "is this old", which is a
different question from "is this still right", and the two come apart in both
directions: a week-old artifact whose inputs never changed is still correct,
and a one-second-old artifact is wrong if an input changed in that second.

Four reasons to regenerate: `no_existing_artifact`, `inputs_changed`,
`producer_version_changed`, and `artifact_corrupt` — the last when the stored
digest is not a well-formed SHA-256, because an untrustworthy record is not a
reason to skip work.

Two details worth the tests they have:

- **Input key order does not force a regeneration.** Digests are taken over
  canonical JSON, so a dict built differently is the same input.
- **List order does.** A list is ordered data, not a set. Treating
  `["a", "b"]` and `["b", "a"]` as the same input would be a guess about what
  the list means.

## Run it

```bash
cd apps/validated-artifact-reuse
python -m unittest test_reuse.py -v
```

All ten tests use a producer spy that counts regenerations: a valid reuse,
changed inputs, a changed producer version, no existing artifact, four
malformed digests, key-order insensitivity, list-order sensitivity, the
generation counter advancing only on regeneration, and every reason coming
from the fixed vocabulary.

# producer-approver-separation

**Atomic claim:** Whoever produced an artifact cannot approve it, and an
approval is bound to the exact digest it covers — a rename, a delegate, or a
later edit all fail closed.

**Inspired by:** independent-review boundaries in governed agent pipelines
(named for context; this app does not import or depend on any other source).
Tier 2, v1.3.

**Enforcement class:** deterministic — normalized identity comparison plus
SHA-256 equality.

## How it works

Both halves are required, and each is useless alone. Separation without
binding lets an approval drift onto a later artifact; binding without
separation lets the producer sign its own work.

`accept(artifact, approval, delegates)` refuses four ways:

- **`self_approval`** — the approver resolves to the producer. Identity is
  compared after normalization, so `Toy-Writer-Agent`, `  toy-writer-agent  `
  and `TOY-WRITER-AGENT` are the same actor. An independence check that a
  respelling defeats is decorative.
- **`self_approval` through a delegate** — `delegates` maps an actor to the
  principal it acts for, and a producer approving through a service account is
  still the producer. This is the realistic shape of the failure: nobody
  types their own name in the approver field, they configure CI to do it.
- **`approval_not_bound`** — the approval names a different artifact's digest,
  or the artifact changed after approval. An approval that survives an edit is
  a signature on a document nobody read.
- **`unattributed_artifact` / `unattributed_approval`** — an unnamed producer
  or approver. Anonymity makes both checks unenforceable, so it is refused at
  the door rather than discovered later.

## Run it

```bash
cd apps/producer-approver-separation
python -m unittest test_separation.py -v
```

All nine tests use toy artifacts and actor names: an independent approval,
self-approval, three respellings, a delegate collapsing to the producer, a
stale approval from another artifact, an approval not surviving an edit, an
unnamed producer, an unnamed approver, and a delegate that is genuinely
independent.

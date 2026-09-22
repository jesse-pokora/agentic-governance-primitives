# hash-pinned-instruction-set

**Atomic claim:** A run executes only under the exact instruction set it
pinned — a single edited byte, an added file, a removed file, or two files
swapping contents all fail closed before the run starts.

**Inspired by:** instruction/prompt pinning in agent runtime attestation
(named for context; this app does not import or depend on any other source).
This is a v1.1 gap-closure app: `deterministic-embedding-contract-check` pins
the exact shape of a model *request*, and nothing pinned the exact
*instructions* the agent ran under.

**Enforcement class:** deterministic — binary pass/fail on SHA-256 equality
per file plus set membership, no fuzzy matching, no fallback.

## How it works

`InstructionManifest.from_files({name: bytes})` records one SHA-256 per
instruction file, bound to the logical name it was loaded under.
`InstructionManifest.digest` hashes the canonical JSON of that whole mapping,
so the digest is independent of insertion order but sensitive to *which* name
carries *which* hash.

`PinnedInstructionSet.pin(manifest)` is what a run records about itself.
`verify(pinned, current)` accepts only on digest equality; on any difference
it raises `InstructionDrift` with a fixed-vocabulary reason — reported in a
fixed precedence (`instruction_removed`, then `instruction_added`, then
`content_drift`, then `manifest_digest_mismatch`) and naming the
lexicographically first offending file, so the same pair of manifests always
produces the same reason and detail.

`run_under(pinned, current, action)` verifies first and calls `action` only
on success, so drift is detected *before* anything executes rather than being
noticed in the audit afterwards.

Two cases are worth singling out, because a looser implementation passes both:

- **Added and removed files count as drift.** An implementation that only
  re-hashes the files it already knows about silently accepts a run with an
  extra instruction file injected into it.
- **Swapping contents between two files is drift.** The multiset of hashes is
  unchanged; only the name→hash binding moved. Hashing contents without
  binding them to names would call that identical.

## Run it

```bash
cd apps/hash-pinned-instruction-set
python -m unittest test_instruction_set.py -v
```

All six tests use toy in-memory instruction files (no real agent instruction
file is read): an exact match, an edited byte, an added file, a removed file,
a content swap, and order-independence of the manifest digest.

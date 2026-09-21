# Agentic Governance Primitives

A collection of small, standalone demonstration apps, each showing **one**
governed-agent-execution concept in isolation. This is its own independent
project — it does not live inside, depend on, or ship code from any other
repository. Its catalog was inspired by governance patterns observed in
Baker Tilly's `Multiagentic-SDLC` (a large agentic-SDLC governance system),
but every app here is built fresh, standalone, and self-contained.

## Why this repo exists

Large agentic governance systems tend to accumulate genuinely reusable
patterns — hash-pinned execution identity, tamper-evident ledgers,
exact-hash approval gates, bounded review escalation, deterministic
reconciliation, persona/capability catalogs, and so on — but those patterns
usually only exist woven into one big multi-agent orchestration system. That
makes them hard to learn from: understanding any one primitive requires
understanding the whole system around it.

This repo inverts that. Each app here demonstrates exactly one primitive,
with no orchestrator, no multi-agent pipeline, and no dependency on any
other codebase. **Bias is toward individual features, not orchestration** —
see [PLAN.md](PLAN.md) for the explicit list of what this repo deliberately
does *not* build (yet).

## Relationship to the Instruction Adherence Bench (IAB)

Baker Tilly's internal IAB proposal (Pokora, v0.5) argues that an
instruction only earns a place in an
always-on agent instruction file if it is followed, needed, worth its cost,
and produces better work — and that every claim should be traceable to a
stable criterion ID, an exact source, and one atomic test (per the companion
*Agentic SDLC POC Grading Rubric*).

This repo borrows that discipline for code, not prose: every app here ships
with a one-sentence **atomic claim** — the single testable thing it proves —
and a note on which real-world pattern inspired it. An app that can't state
its atomic claim in one sentence is scoped wrong.

## Reference documents

The [Docs/](Docs) folder holds the source documents this repo's discipline is
based on:

- [IAB-proposal-2pp.docx](Docs/IAB-proposal-2pp.docx) — the short-form
  Instruction Adherence Bench proposal.
- [Instruction-Adherence-Bench-proposal.docx](Docs/Instruction-Adherence-Bench-proposal.docx) —
  the full IAB proposal (Pokora, v0.5).
- [Agentic-SDLC-POC-Grading-Rubric.docx](Docs/Agentic-SDLC-POC-Grading-Rubric.docx) —
  the companion grading rubric each app's atomic claim is written to satisfy.
- [Repository-Summary-Atomic-Instruction-Test-Matrix.docx](Docs/Repository-Summary-Atomic-Instruction-Test-Matrix.docx) —
  the atomic-instruction test matrix referenced by the rubric.

## Layout

```
agentic-governance-primitives/
  README.md          this file
  PLAN.md             the full decomposition catalog and build phasing
  Docs/               reference documents (IAB proposal, grading rubric, test matrix)
  apps/               one directory per demo app (created as each is built)
```

## Status

Phase 1 built. See [PLAN.md](PLAN.md) for the full catalog, phasing, and
source mapping.

| App | Enforcement | Status |
|---|---|---|
| [hash-pinned-identity](apps/hash-pinned-identity) | deterministic | built |
| [exact-plan-approval-gate](apps/exact-plan-approval-gate) | deterministic | built |
| [authenticated-transition-ledger](apps/authenticated-transition-ledger) | deterministic | built |
| [bounded-review-epoch-escalation](apps/bounded-review-epoch-escalation) | deterministic | built |

The remaining 14 apps in Phases 2–4 are planned but not yet scaffolded.

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

## Start here

Open [index.html](index.html) in a browser: the whole catalog, grouped by tier
and criticality, with a five-app reading path and a link to every demo. No
server, no build step.

[METHOD.md](METHOD.md) is the other half — how an app here is written, and how
to tell whether a new one is scoped right.

## Running the catalog

```bash
python run_all.py                  # every app and composition
python run_all.py --demos          # also re-record demos and check byte-stability
python tools/generate_docs.py --check   # are the docs in sync with claims.json?
python tools/generate_index.py --check   # is index.html in sync?

npm install && npx playwright install chromium
npx playwright test                # every demo page against its recording
```

[claims.json](claims.json) is the single source of truth for every app's
claim, tier, release, enforcement class and standards mapping. The catalog
tables in this file and in [CONFORMANCE.md](CONFORMANCE.md) are generated from
it into a managed region — via this repo's own
[managed-block-confinement](apps/managed-block-confinement) app, so the prose
around them stays exactly as written. CI fails if they drift apart, which is
the only durable answer to the same facts living in several documents.

## Demo pages

Every app ships an animated page demonstrating its atomic claim — open
`apps/<app>/demo.html` in a browser. The pages contain no app logic: each one
animates a trace recorded by running that app's real Python module, so a page
cannot show an outcome the code does not produce. A Playwright suite checks
every page against its recording, including the exact denial reason each
module raised. See [demos/](demos) for the workflow.

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

All 43 apps built — 18 in v1, 11 in v1.1 closing gaps the v1 catalog left open,
4 in v1.2 constraining model behavior rather than securing it, and 10 in v1.3
derived from a real agent's atomic instruction and test matrix. Each
is still one atomic claim, standalone, and off the out-of-scope list. See
[PLAN.md](PLAN.md) for the full catalog, phasing, and source mapping, and
[CONFORMANCE.md](CONFORMANCE.md) for how each app maps to published
standards.

<!-- BEGIN MANAGED BLOCK -->
| App | Enforcement | Status |
|---|---|---|
| [authenticated-transition-ledger](apps/authenticated-transition-ledger) | deterministic | built |
| [deterministic-primitives-kit](apps/deterministic-primitives-kit) | deterministic | built |
| [exact-plan-approval-gate](apps/exact-plan-approval-gate) | deterministic | built |
| [execution-lock-and-recovery](apps/execution-lock-and-recovery) | deterministic | built |
| [governed-preflight-denial-evidence](apps/governed-preflight-denial-evidence) | deterministic | built |
| [hash-pinned-identity](apps/hash-pinned-identity) | deterministic | built |
| [safe-failure-diagnostics](apps/safe-failure-diagnostics) | deterministic | built |
| [workspace-attestation](apps/workspace-attestation) | deterministic | built |
| [bounded-review-epoch-escalation](apps/bounded-review-epoch-escalation) | deterministic | built |
| [canonical-outcome-reconciliation](apps/canonical-outcome-reconciliation) | deterministic | built |
| [non-overlapping-error-mapping](apps/non-overlapping-error-mapping) | deterministic | built |
| [trusted-revision-anchor](apps/trusted-revision-anchor) | deterministic | built |
| [typed-ledger-slot-supersession](apps/typed-ledger-slot-supersession) | deterministic | built |
| [governed-context-provenance](apps/governed-context-provenance) | deterministic | built |
| [persona-capability-catalog](apps/persona-capability-catalog) | informational | built |
| [single-purpose-adversarial-reviewer](apps/single-purpose-adversarial-reviewer) | hybrid | built |
| [deterministic-embedding-contract-check](apps/deterministic-embedding-contract-check) | deterministic | built |
| [prompt-injection-scanner-mcp](apps/prompt-injection-scanner-mcp) | hybrid | built |


### v1.1 — gap closure

Derived from this catalog's own criteria rather than observed in a source
system: each closes a gap the v1 apps leave open.

| App | Enforcement | Status |
|---|---|---|
| [generated-code-admission-gate](apps/generated-code-admission-gate) | deterministic | built |
| [hash-pinned-instruction-set](apps/hash-pinned-instruction-set) | deterministic | built |
| [pinned-egress-allowlist](apps/pinned-egress-allowlist) | deterministic | built |
| [verified-secret-redaction](apps/verified-secret-redaction) | deterministic | built |
| [write-scope-confinement](apps/write-scope-confinement) | deterministic | built |
| [attested-rollback-checkpoint](apps/attested-rollback-checkpoint) | deterministic | built |
| [bounded-execution-budget](apps/bounded-execution-budget) | deterministic | built |
| [concurrent-append-integrity](apps/concurrent-append-integrity) | deterministic | built |
| [deterministic-ledger-replay](apps/deterministic-ledger-replay) | deterministic | built |
| [forward-only-revert-journal](apps/forward-only-revert-journal) | deterministic | built |
| [capability-gated-tool-invocation](apps/capability-gated-tool-invocation) | deterministic | built |


### v1.2 — model-behavior constraint & drift detection

Reliability rather than security: the deterministic gates a nondeterministic
model is wrapped in, so its output becomes predictable.

| App | Enforcement | Status |
|---|---|---|
| [grounded-claim-verification](apps/grounded-claim-verification) | deterministic | built |
| [measured-token-accounting](apps/measured-token-accounting) | deterministic | built |
| [memory-conflict-quarantine](apps/memory-conflict-quarantine) | deterministic | built |
| [tiered-model-escalation-gate](apps/tiered-model-escalation-gate) | hybrid | built |


### v1.3 — derived from an atomic instruction and test matrix

Found by reading a 192-criterion instruction-adherence matrix for one real
governed agent and asking which of its themes had no teaching app here.

| App | Enforcement | Status |
|---|---|---|
| [argv-not-shell-invocation](apps/argv-not-shell-invocation) | deterministic | built |
| [managed-block-confinement](apps/managed-block-confinement) | deterministic | built |
| [reduced-child-environment](apps/reduced-child-environment) | deterministic | built |
| [staged-input-allowlist](apps/staged-input-allowlist) | deterministic | built |
| [unproven-isolation-fails-closed](apps/unproven-isolation-fails-closed) | deterministic | built |
| [canonical-output-shape](apps/canonical-output-shape) | deterministic | built |
| [optional-input-does-not-block](apps/optional-input-does-not-block) | deterministic | built |
| [producer-approver-separation](apps/producer-approver-separation) | deterministic | built |
| [provable-dry-run](apps/provable-dry-run) | deterministic | built |
| [validated-artifact-reuse](apps/validated-artifact-reuse) | deterministic | built |


### v1.4 — the multi-agent risks, as primitives

The risks that involve more than one agent, built as contracts rather than as
an orchestrator: an envelope is not a bus, and a breaker is not a scheduler.

| App | Enforcement | Status |
|---|---|---|
| [failure-bulkhead](apps/failure-bulkhead) | deterministic | built |
| [authenticated-agent-message](apps/authenticated-agent-message) | deterministic | built |
| [delegation-scope-attenuation](apps/delegation-scope-attenuation) | deterministic | built |
| [declared-objective-conformance](apps/declared-objective-conformance) | deterministic | built |


### v1.5 — instruction adherence, gated deterministically

Whether an agent followed the instructions that define what it does. The part
that is mechanically checkable is gated here; the part that is not is reported
as unchecked rather than quietly assumed.

| App | Enforcement | Status |
|---|---|---|
| [absent-evidence-is-not-compliance](apps/absent-evidence-is-not-compliance) | deterministic | built |
| [falsifiable-instruction-check](apps/falsifiable-instruction-check) | deterministic | built |
| [instruction-policy-gate](apps/instruction-policy-gate) | deterministic | built |
| [permissive-contract-is-a-gap](apps/permissive-contract-is-a-gap) | deterministic | built |
<!-- END MANAGED BLOCK -->

## What the catalog adds up to

Sorted by function rather than by tier, the apps converge on a **control
plane**, not an agent architecture: identity and integrity, authorization,
audit and evidence, containment and recovery, input trust, contract
verification, and — since v1.2 — measurement and drift detection around the
model itself. That is deliberate. Agent frameworks ship the loop, the
messages, and the state graph and almost none of this; this repo ships the
half they don't, in a form you can put in front of an agent you already have.

Two halves of the same job: Tiers 1–4 constrain what an agent is *permitted*
to do, and Tier 5 constrains how far its output may drift from what the system
knows. A governed agent that is unpredictable is not governed.

v1.3 adds a third thing the catalog was missing: restraint about refusing.
[optional-input-does-not-block](apps/optional-input-does-not-block) is the only
app here whose lesson is when *not* to fail closed. It exists because 33
demonstrations of refusing is a curriculum that produces agents nobody can
start, and knowing what not to block on is the harder half — the failure is
invisible in review, since nobody files a bug saying that something refused
correctly but should not have.

What the catalog therefore does *not* contain, and will not by accident: an
agent loop, an inter-agent channel, a router, shared working memory, or a
second persona. Those are the defining pieces of a multi-agent architecture,
and four of the five are already on PLAN.md's out-of-scope list.

[CONFORMANCE.md](CONFORMANCE.md) also compares this catalog to
[microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit),
the largest project in this space: a framework where the governance properties
live inside it, against a catalog where each property is one claim with one
runnable test. Their coverage profiles turn out to be close to complementary.

Composing a few of these into a minimal pipeline is a possible future step
(see PLAN.md's "Relationship to future IAB work"), not a default.

# Agentic Governance Primitives

**An executable assurance case for agent governance.** Fifty-nine controls,
each stated as one testable claim, each with a test that fails if the claim
stops being true, and each with a page that animates the real code enforcing
it.

Governance claims are usually prose. "We enforce least privilege" is a
sentence; nobody can run it. Every claim here is a sentence *and* an
executable, and where a claim cannot be made deterministically the repo says
so rather than rounding up.

## Reading this in ten minutes

If you are assessing this rather than using it, these six artifacts carry the
argument. They are chosen for the claims they **decline** to make.

| Read | For |
|---|---|
| [generated-code-admission-gate](apps/generated-code-admission-gate) | Opens by refusing its own most attractive claim: an admission gate is not a sandbox, and saying otherwise would make it the most dangerous app here |
| [structural-duplicate-detection](apps/structural-duplicate-detection) | States what it cannot catch, and why a similarity threshold would not be deterministic however carefully the number is picked |
| [optional-input-does-not-block](apps/optional-input-does-not-block) | Built as a counterweight after 33 apps of refusing, because a catalog that only teaches fail-closed produces agents that cannot start |
| [CONFORMANCE.md](CONFORMANCE.md) | Maps to OWASP ASI 2026, NIST SP 800-53 and ISO/IEC 42001 — and defines "covered" as *one control demonstrated*, never *the risk handled* |
| [PLAN.md](PLAN.md) | Records a scope rule being misread for three revisions, and the correction: "The rule did not change; the reading of it was wrong" |
| [METHOD.md](METHOD.md) | The transferable part — how a claim is scoped, and the one-sentence test that says when an app should be split |

## How this was built

Directed and reviewed by [Jesse Pokora](https://github.com/jesse-pokora),
written with Claude (Anthropic) as a pair, over two days. Every commit carries
the co-authorship; none of it is concealed, because the interesting work is not
the typing.

What the history shows, if you want to check the direction rather than take it
on trust:

- **Scope corrections.** Three agentic risks were filed as out-of-scope on a
  misreading of this repo's own rule; commit `71ed122` reverses that and
  explains why an envelope is not a bus.
- **Claims cut back under evidence.** CI regenerating a demo on Linux revealed
  that `reduced-child-environment` could not claim what its README implied;
  commit `c4c6195` narrows the claim rather than working around the finding.
- **The catalog turned on itself.** `tools/self_check.py` runs this repo's own
  duplicate detector over its own 324 functions, finds a genuine redundancy,
  and records which of the other findings are deliberate.
- **Tests that test the mechanism.** The no-shell check parses its own module's
  AST rather than grepping it, because the prose mentions `shell=True` in order
  to say it is never used.

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

## What this is, and what it is not

Governing an agent is four jobs, and they get conflated constantly. Naming them
is the fastest way to see what this catalog covers:

| Job | What it means | Here? |
|---|---|---|
| **Enforce** | The gate refuses. The effect does not happen. | Yes — most of the catalog |
| **Attest** | What happened is provable and tamper-evident afterwards. | Yes — the ledger and attestation apps |
| **Measure outcomes** | How often it refused, how many refusals were wrong, what it cost. | **No** — see [agentic-governance-outcomes](https://github.com/jesse-pokora/agentic-governance-outcomes) |
| **Audit the claim** | Is the compliance report itself trustworthy? | Yes — the v1.5 instruction-adherence apps |

The third row is a deliberate hole, not an oversight. A rate like "99.9% policy
compliance over 24 hours" requires real runs at real volume; no amount of
further building here produces one, because a demonstration needs a fixture and
a measurement needs traffic.

It has its own repository —
[agentic-governance-outcomes](https://github.com/jesse-pokora/agentic-governance-outcomes)
— which builds the instrument and the preconditions a rate needs before it means
anything: a reconciled denominator, attributable refusals, and a window, sample
floor and budget fixed before the number is computed. Its harness reads this
catalog's 319 recorded decisions, and its README is explicit that a refusal rate
over demo recordings measures how a catalog chose to demonstrate itself.

**Enforcement is not correctness.** A gate is subtractive: it removes
possibilities. `write-scope-confinement` stops a write leaving a directory and
has no opinion on whether the file is any good; `exact-plan-approval-gate`
binds an approval to a plan and cannot tell you the plan was sensible. What
enforcement buys is a bounded blast radius and an attributable refusal — never
a correct agent. Everything about whether the work was *good* lives in
measurement, and measurement of a stochastic system is probabilistic.

**This is a teaching catalog, not infrastructure.** Every app runs against toy
fixtures. None is a production control, and running them proves nothing about
any system that has not adopted them. For governing real agents in production,
[microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit)
is a serious, actively maintained implementation — see the comparison in
[CONFORMANCE.md](CONFORMANCE.md), which also records where its coverage and
this catalog's differ.

## The instruction-adherence thesis

An instruction earns its place in an always-on agent instruction file only if
it is **followed**, **needed**, worth its cost, and produces better work — and
every claim about it should be traceable to a stable criterion ID, an exact
source, and one atomic test.

That argument is not this repository's; it comes from prior unpublished work of
the author's on measuring instruction adherence. What this repo does is borrow
the discipline for code rather than prose: every app here ships
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

## Where the conventions came from

The claim discipline here — one atomic claim per app, a stable identifier, an
exact source, one test — derives from earlier unpublished work of the author's:
a proposal for measuring instruction adherence, a grading rubric that
accompanies it, and a 192-criterion atomic instruction and test matrix written
for a single governed agent.

**None of that material is distributed with this repository**, and the catalog
is built so it does not need to be. Every app states its own claim, and
[METHOD.md](METHOD.md) carries the conventions in full without reproducing any
source.

The matrix mattered most: the v1.3 and v1.5 apps were found by reading it and
asking which of its themes had no teaching app here.

## Layout

```
agentic-governance-primitives/
  README.md           this file
  METHOD.md           how an app here is written, and how to scope a new one
  CONFORMANCE.md      mapping to OWASP ASI 2026, NIST SP 800-53, ISO/IEC 42001
  PLAN.md             the catalog, its phasing, and what is deliberately excluded
  index.html          the front door: every app, by tier and criticality
  apps/               one directory per app
  compositions/       the one artifact that shows the apps composing
  demos/              the recorder, renderer, diagrams and Playwright suite
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
| [composition-root-construction](apps/composition-root-construction) | deterministic | built |
| [ablation-required-for-causal-claim](apps/ablation-required-for-causal-claim) | deterministic | built |
| [absent-evidence-is-not-compliance](apps/absent-evidence-is-not-compliance) | deterministic | built |
| [deterministic-checker-contract](apps/deterministic-checker-contract) | deterministic | built |
| [falsifiable-instruction-check](apps/falsifiable-instruction-check) | deterministic | built |
| [instruction-policy-gate](apps/instruction-policy-gate) | deterministic | built |
| [permissive-contract-is-a-gap](apps/permissive-contract-is-a-gap) | deterministic | built |
| [repeat-reliability-predeclared](apps/repeat-reliability-predeclared) | deterministic | built |
| [traceable-instruction-source](apps/traceable-instruction-source) | deterministic | built |
| [enforcement-mechanism-attribution](apps/enforcement-mechanism-attribution) | deterministic | built |
| [structural-duplicate-detection](apps/structural-duplicate-detection) | deterministic | built |
| [telemetry-is-not-cost](apps/telemetry-is-not-cost) | deterministic | built |
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

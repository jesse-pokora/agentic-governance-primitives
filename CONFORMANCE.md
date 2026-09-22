# Conformance mapping

Every app in this repo carries an atomic claim — one testable sentence. This
document maps each claim to named criteria in published standards, so the
catalog can be read as a conformance suite rather than as a personal catalog.

## What this is, and what it is not

**This is an interpretive mapping made by this repo's author.** It is not an
assessment, not a certification, and not an audit opinion. Nobody accredited
has reviewed it.

**A demonstration app is not an implementation.** Each app proves that a
control *can* be enforced deterministically, with a test a skeptic can run in
seconds. None of them is a production control, and none of them makes a system
that imports it compliant with anything. The honest reading of a row below is
"this app demonstrates the property this criterion asks for", not "this app
satisfies this criterion".

**Identifiers should be checked against the standard text.** The OWASP ASI and
NIST SP 800-53 identifiers here were verified against the sources listed at the
end. The ISO/IEC 42001 Annex A numbering was verified against secondary sources
rather than the standard itself, which is paywalled — treat those cells as
clause-level pointers and confirm them before citing them anywhere that
matters.

## Frameworks used

| Framework | Version | Why it is here |
|---|---|---|
| **OWASP Top 10 for Agentic Applications** (`ASI01`–`ASI10`) | 2026 | The closest published risk taxonomy to what this repo governs. Agent-specific rather than LLM-specific. |
| **NIST SP 800-53** | Rev. 5 | Precise, stable control identifiers. These primitives *are* classic security controls, and 800-53 names them better than any AI-specific framework does. |
| **ISO/IEC 42001** Annex A | 2023 | The management-system level — what an auditor actually asks an organization for. |

The **OWASP Top 10 for LLM Applications** is deliberately not used as a per-app
anchor. A 2026 edition exists and reorders the 2025 list (Excessive Agency moved
from LLM06 to third, Unbounded Consumption from LLM10 to sixth), so citing the
2025 numbering would date this document immediately. The ASI list covers the
same ground for agents.

**NIST AI RMF** is not mapped per app. Its subcategory identifiers were not
verified here, and guessing at them would defeat the purpose of the exercise.
At the function level the catalog sits almost entirely in MEASURE and MANAGE.

## The mapping

Strength column: **direct** — the app demonstrates the criterion's core
property; **partial** — it demonstrates one part of it; **adjacent** — it
supports the criterion without demonstrating it.

### Tier 1 — Deterministic security primitives

| App | OWASP ASI (2026) | NIST SP 800-53 Rev 5 | ISO/IEC 42001 Annex A | Strength |
|---|---|---|---|---|
| hash-pinned-identity | ASI04, ASI05 | SI-7, SR-4, SR-11, CM-5 | A.6.2.5 | direct |
| exact-plan-approval-gate | ASI09, ASI10 | AC-3, CM-3 | A.9.2, A.9.4 | direct |
| authenticated-transition-ledger | ASI10 | AU-9, AU-10, SR-9 | A.6.2.8 | direct |
| governed-preflight-denial-evidence | — | AU-3, AU-9 | A.6.2.8 | direct |
| safe-failure-diagnostics | — | AU-3, SI-11 | A.6.2.8 | direct |
| execution-lock-and-recovery | ASI08 | CP-10, AC-3 | A.6.2.6 | partial |
| deterministic-primitives-kit | — | SI-10 | A.6.2.4 | adjacent |
| workspace-attestation | ASI05 | SI-7, CM-3, AU-12 | A.6.2.6 | direct |
| hash-pinned-instruction-set | ASI01, ASI04 | CM-3, CM-5, SI-7 | A.6.2.7 | direct |
| pinned-egress-allowlist | ASI02, ASI04 | SC-7, AC-4 | A.6.2.6 | direct |
| write-scope-confinement | ASI02, ASI05 | AC-3, AC-6, SC-7 | A.6.2.6 | direct |
| verified-secret-redaction | — | AC-4, SC-28, AU-9 | A.6.2.6 | direct |
| generated-code-admission-gate | ASI05 | SI-7, SI-10, CM-7 | A.6.2.4 | direct |
| managed-block-confinement | ASI02 | AC-3, CM-5, SI-7 | A.6.2.6 | direct |
| staged-input-allowlist | ASI04, ASI06 | AC-4, SC-7, SI-10 | A.6.2.6 | direct |
| unproven-isolation-fails-closed | ASI05 | CM-7, SA-11, AU-10 | A.6.2.4 | direct |
| argv-not-shell-invocation | ASI05 | SI-10, CM-7 | A.6.2.5 | direct |
| reduced-child-environment | — | AC-6, SC-28, CM-7 | A.6.2.5 | direct |

### Tier 2 — Review & process governance

| App | OWASP ASI (2026) | NIST SP 800-53 Rev 5 | ISO/IEC 42001 Annex A | Strength |
|---|---|---|---|---|
| bounded-review-epoch-escalation | ASI09, ASI10 | AC-3, CM-3 | A.9.2 | direct |
| non-overlapping-error-mapping | — | SI-10, SI-11 | A.6.2.4 | adjacent |
| canonical-outcome-reconciliation | — | AU-12, SI-10 | A.6.2.4 | adjacent |
| trusted-revision-anchor | ASI04 | CM-3, SI-7, SR-4 | A.6.2.5 | direct |
| typed-ledger-slot-supersession | ASI03 | AC-3, AU-9, CM-5 | A.6.2.8 | direct |
| bounded-execution-budget | ASI10 | SC-5, AC-3 | A.6.2.6 | direct |
| deterministic-ledger-replay | ASI06 | AU-9, AU-10, SI-7 | A.6.2.8 | direct |
| attested-rollback-checkpoint | ASI08 | CP-10, SI-7 | A.6.2.6 | direct |
| forward-only-revert-journal | ASI08 | AU-9, AU-11, SR-9 | A.6.2.8 | direct |
| concurrent-append-integrity | — | AU-9, AU-12 | A.6.2.8 | direct |
| optional-input-does-not-block | — | SI-10, CP-2 | A.9.2 | adjacent |
| producer-approver-separation | ASI03, ASI09 | AC-5, AU-10, CM-3 | A.9.2 | direct |
| provable-dry-run | ASI02 | CM-3, AU-12 | A.6.2.4 | direct |
| canonical-output-shape | ASI09 | SI-10 | A.6.2.4 | direct |
| validated-artifact-reuse | ASI04 | SI-7, CM-3 | A.6.2.6 | direct |

### Tier 3 — Persona & agent architecture

| App | OWASP ASI (2026) | NIST SP 800-53 Rev 5 | ISO/IEC 42001 Annex A | Strength |
|---|---|---|---|---|
| persona-capability-catalog | ASI03 | AC-2, AC-6 | A.3.2 | direct |
| single-purpose-adversarial-reviewer | ASI09 | SA-11 | A.6.2.4 | adjacent |
| governed-context-provenance | ASI01, ASI06 | AC-16, SI-10, SR-4 | A.6.2.6 | direct |
| capability-gated-tool-invocation | ASI02, ASI03 | AC-3, AC-6 | A.9.4 | direct |

### Tier 4 — Domain example

| App | OWASP ASI (2026) | NIST SP 800-53 Rev 5 | ISO/IEC 42001 Annex A | Strength |
|---|---|---|---|---|
| deterministic-embedding-contract-check | ASI04 | SI-7, SR-4 | A.6.2.4 | direct |
| prompt-injection-scanner-mcp | ASI01 | SI-10 | A.6.2.6 | partial |

### Tier 5 — Model-behavior constraint & drift detection

| App | OWASP ASI (2026) | NIST SP 800-53 Rev 5 | ISO/IEC 42001 Annex A | Strength |
|---|---|---|---|---|
| measured-token-accounting | ASI10 | AU-12, SC-5 | A.6.2.6 | direct |
| grounded-claim-verification | ASI06, ASI09 | SI-10, AC-16, SR-4 | A.6.2.4 | direct |
| memory-conflict-quarantine | ASI06 | SI-7, AU-9 | A.6.2.6 | direct |
| tiered-model-escalation-gate | ASI09, ASI10 | SI-10, AU-12 | A.6.2.4 | direct |

## Coverage against OWASP ASI 2026

This is what a conformance suite is actually for: not what it covers, but what
it does not.

| Risk | Coverage | Notes |
|---|---|---|
| **ASI01** Agent Goal Hijack | covered | prompt-injection-scanner-mcp, governed-context-provenance, hash-pinned-instruction-set |
| **ASI02** Tool Misuse & Exploitation | covered | capability-gated-tool-invocation, pinned-egress-allowlist, write-scope-confinement |
| **ASI03** Agent Identity & Privilege Abuse | covered | persona-capability-catalog, capability-gated-tool-invocation, hash-pinned-identity |
| **ASI04** Agentic Supply Chain Compromise | covered | hash-pinned-identity, trusted-revision-anchor, deterministic-embedding-contract-check |
| **ASI05** Unexpected Code Execution | covered | generated-code-admission-gate inspects model-generated code before it is compiled; argv-not-shell-invocation removes the shell from the launch; unproven-isolation-fails-closed refuses to treat an assertion of isolation as evidence of it. Admission and launch shape, not containment — that boundary is stated in each app's README. |
| **ASI06** Memory & Context Poisoning | covered | governed-context-provenance, memory-conflict-quarantine, deterministic-ledger-replay |
| **ASI07** Insecure Inter-Agent Communication | **not covered** | There is no inter-agent channel in this repo, by design. A message bus is orchestration, which PLAN.md places out of scope. This gap is a consequence of that decision, not an oversight. |
| **ASI08** Cascading Agent Failures | **partial** | bounded-execution-budget, execution-lock-and-recovery, and the rollback pair limit blast radius within one run. Cascades *between* agents need more than one agent. |
| **ASI09** Human-Agent Trust Exploitation | covered | exact-plan-approval-gate, grounded-claim-verification, bounded-review-epoch-escalation |
| **ASI10** Rogue Agents | **partial** | Budgets, escalation caps, and ledgers detect drift from declared policy. "Rogue" presupposes a degree of autonomy this repo does not model. |

Three of the ten are partial or uncovered, and every one of them traces to the
same root: this repo governs **one** agent's execution, while those risks are
about **several** agents interacting. That is the honest boundary of a
primitives catalog that deliberately excludes orchestration — and it is now the
*only* reason for a gap, since ASI05, the one shortfall that was a genuinely
missing primitive, is closed.

## Related work: Microsoft Agent Governance Toolkit

The largest project in this space is
[microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit)
(AGT) — a runtime governance toolkit with a policy engine, SDKs for Python,
TypeScript, .NET, Go and Rust, and packages on PyPI, npm and NuGet, governed by
a technical steering committee and currently in public preview. It maps itself
to the same ASI 2026 taxonomy used above.

Naming it here is deliberate. A conformance document that ignores the biggest
implementation of what it describes is less useful, not more.

### How the two differ

AGT is a **framework**: you install it, and the governance properties are
enforced inside it. This repo is an **executable assurance case**: each property
is isolated as one claim with one runnable test, so a property can be understood
and checked without adopting anything.

The difference shows up in what each offers as evidence. AGT's ASI mapping cites
links to source files. This repo's rows cite a test you can run in seconds that
fails if the claim is false. Neither is better in general — they answer different
questions. "How do I govern my agent in production" is AGT's question. "What
exactly does this control guarantee, and how would I know if it stopped holding"
is this repo's.

### Complementary coverage

AGT's self-assessment reports **7 of 10 ASI risks Full, 3 Partial, 0 gaps** (its
repository description states 10/10; this comparison uses the project's own
mapping document, which is the more conservative and more recent figure). Set
against the coverage table above, the two profiles are close to complementary:

| Risk | AGT | This repo |
|---|---|---|
| ASI07 Inter-agent communication | Full — DID trust gate | not covered — orchestration is out of scope |
| ASI08 Cascading failures | Full — circuit breaker, rate limiter | partial |
| ASI04 Agentic supply chain | Partial — "no SBOM" | covered — three apps |
| ASI06 Memory & context poisoning | Partial — "integration is opt-in" | covered — three apps |
| ASI09 Human-agent trust | Partial — "no universal UI integration" | covered — three apps |

AGT is strongest where this repo is weakest (anything involving more than one
agent), and partial in three places where this repo has direct coverage.

### The gap Tier 5 sits in

AGT's `LIMITATIONS.md` states its boundary plainly, and the statement is worth
quoting because it is unusually candid for a project of its size:

> AGT governs **what agents do** (tool calls, resource access, inter-agent
> messages). It does **not** govern what agents *think* or *say*. [...] AGT does
> **not** detect if the *content* passed to an allowed tool is a hallucination.

That is the boundary between action governance and content fidelity, and Tier 5
of this catalog sits entirely on the far side of it.
`grounded-claim-verification` checks whether an assertion is anchored to a held
record; `memory-conflict-quarantine` refuses to let a later assertion silently
replace an earlier one; `tiered-model-escalation-gate` refuses output that fails
a declared check regardless of which tier produced it. None of those is a
security control, and the largest toolkit in the field states that it does not
cover them.

*Assessed September 2026 against the repository's README, charter, ASI mapping,
independence and limitations documents. The source was not reviewed.*

## Where the v1.3 apps came from

The v1.1 and v1.2 apps were found by reasoning about the catalog. The v1.3 set
was found differently: by reading an atomic instruction and test matrix for one
real governed agent — 192 criteria, each bound to a source file and line range,
each with a named unit test, an enforcement class and a criticality tier — and
asking which of its themes had no teaching app here.

Most did. Untrusted-evidence handling, approval for irreversible actions,
capability denial, claims supported by inspected evidence, reported-versus-
actual reconciliation, token counting exactly once: all already had one. Ten
themes did not, and those became the v1.3 apps.

That exercise is worth repeating against any real matrix, because it finds a
different class of gap than reasoning does. Reasoning about a catalog surfaces
what is *missing from a pattern*; reading a real matrix surfaces what a real
system had to say out loud — including
[optional-input-does-not-block](../apps/optional-input-does-not-block), whose
lesson is the one a catalog of governance primitives is structurally least
likely to reach on its own.

## Relationship to the Instruction Adherence Bench

IAB's registry needs, per instruction, a stable criterion ID traceable to an
exact source and one atomic test. Every app here already carries the atomic
test and the claim; this document supplies the external criterion ID. An app's
row is therefore a complete registry record: claim, criterion, test.

## Sources

- [OWASP Top 10 for Agentic Applications 2026 — OWASP Gen AI Security Project](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [OWASP Top 10 for Agents 2026, ASI01–ASI10 list — DeepTeam](https://www.trydeepteam.com/docs/frameworks-owasp-top-10-for-agentic-applications)
- [OWASP GenAI LLM Top 10 2026 — OWASP Gen AI Security Project](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)
- [OWASP Top 10 for LLM Applications 2025 (PDF)](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf)
- [NIST SP 800-53 Rev. 5 — NIST CSRC](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- [NIST SP 800-53 Rev 5 control families and titles — CSF Tools](https://csf.tools/reference/nist-sp-800-53/r5/)
- [ISO 42001 Annex A controls — ISMS.online](https://www.isms.online/iso-42001/annex-a-controls/)
- [ISO 42001 Annex A control A.9, Use of AI systems — ISMS.online](https://www.isms.online/iso-42001/annex-a-controls/a-9-use-of-ai-systems/)
- [microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit)
- [AGT — OWASP Agentic Security Initiative reference architecture (its ASI 2026 self-assessment)](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/compliance/owasp-agentic-top10-architecture.md)
- [AGT — Known Limitations & Design Boundaries](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/LIMITATIONS.md)

Identifiers verified September 2026.

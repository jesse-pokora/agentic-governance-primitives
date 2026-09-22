# capability-gated-tool-invocation

**Atomic claim:** A tool call runs only if the calling persona's declared
capability set contains that tool's exact required capability — and a denied
call never enters the tool function at all.

**Inspired by:** capability mediation in declarative persona/agent catalogs
(named for context; this app does not import or depend on any other source).
This is a v1.1 gap-closure app and the enforcement half of
[persona-capability-catalog](../persona-capability-catalog), which declares
who *may* do what but never denies anything.

**Enforcement class:** deterministic — exact string membership in a frozen
capability set, no prefix match, no wildcard expansion, no case folding.

## How it works

`CapabilityGate(personas, tools)` copies the catalog into immutable
structures at construction: each persona's capabilities become a `frozenset`,
so neither the caller's original dict nor the set handed back by
`capabilities_of` can be mutated into a grant.

`invoke(persona, tool_name, ...)` runs three checks in a fixed order —
`unknown_persona`, `unknown_tool`, `capability_not_granted` — so the same call
always produces the same denial reason. Only after all three pass is
`tool.fn` called.

Two properties are what make this more than a lookup:

- **Denial precedes execution.** Every test tool is a spy that counts entries
  into its body. A denied call leaves that count at zero, which distinguishes
  a real gate from a post-hoc audit that notices the violation after the side
  effect has already landed.
- **The catalog is the only authority.** Mutating the `personas` dict after
  construction — the shape a runtime privilege-escalation attempt takes — is
  tested to grant nothing.

Capability strings are compared exactly. `repo.read` does not imply
`repo.read_secrets`, and `repo.*` grants nothing, because a gate that
interprets structure in capability names turns every new tool name into a
silent policy change.

## Run it

```bash
cd apps/capability-gated-tool-invocation
python -m unittest test_capability_gate.py -v
```

All eight tests use toy in-process tools (no real repository, secret, or
deployment): a granted call, an ungranted call, a prefix near-miss, a
wildcard, an unknown persona, an unknown tool, post-construction mutation of
the catalog, and immutability of a returned capability set.

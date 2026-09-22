# delegation-scope-attenuation

**Atomic claim:** Authority can only shrink as it is delegated — each link in a
chain may hold a subset of what the link before it held, never a capability its
delegator did not have.

**Inspired by:** capability attenuation in delegated-authority systems (named
for context; this app does not import or depend on any other source). Tier 3,
v1.4.

**Enforcement class:** deterministic — set containment along a chain.

## How it works

This is the rule that makes delegation safe to allow at all. Without it, an
agent handing work to a sub-agent is a laundering step: the sub-agent asks for
more than its delegator could have asked for, and nothing on the receiving end
can tell the difference.

`effective_authority(chain)` walks from the root grant outward and returns what
survived. It refuses three ways:

- **`amplified_capability`** — a link claims something its delegator did not
  hold. The denial names the capability and the depth, because the added
  capability is the thing a reader needs to see, not the link number.
- **`delegation_loop`** — an actor appears twice. A loop lets authority be
  re-derived from a later link, which is amplification wearing a longer path.
- **`empty_chain`** — no root grant to attenuate from.

Capability names are compared exactly, so `repo.read` does not permit
`repo.read_secrets` — the same rule as
[capability-gated-tool-invocation](../capability-gated-tool-invocation), for
the same reason: a gate that reads structure into capability names turns every
new name into a silent policy change.

Attenuating all the way to nothing is legal. An agent may delegate the
obligation to do something while delegating none of the authority to act, and
the resulting empty set is a correct answer rather than an error.

## Run it

```bash
cd apps/delegation-scope-attenuation
python -m unittest test_delegation.py -v
```

All ten tests use toy capability sets: an attenuating chain, an amplifying
link, a root grant, an unchanged link, amplification deep in a long chain,
attenuation to nothing, a loop, an empty chain, `may()` answering only for
surviving capabilities, and an exact-name near miss.

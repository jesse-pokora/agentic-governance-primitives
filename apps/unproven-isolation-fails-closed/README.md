# unproven-isolation-fails-closed

**Atomic claim:** A run proceeds only when isolation is verified by a probe
that actually ran — an operator assertion and a child's capability
declaration are recorded for audit and contribute nothing to the verdict.

**Inspired by:** sandbox-assertion and capability-declaration boundaries in
governed agent runners (named for context; this app does not import or depend
on any other source). Tier 1, v1.3.

**Enforcement class:** deterministic — the verdict is a function of probe
results only.

## The distinction

A claim about the world and a measurement of the world are different objects.
A governance system that stores them in the same field has already lost the
argument, because from then on nothing can tell "we checked" from "somebody
said".

Three things are kept apart here:

- **`Probe`** — a named check that ran and returned a result. The only input
  to the verdict.
- **`Assertion`** — somebody, possibly a command-line flag, said isolation is
  in place. Recorded, never counted.
- **`CapabilityDeclaration`** — what a child process says about itself. A
  child advertising that it denies writes and terminals is describing its own
  protocol, not the operating system it runs on. An honest child is telling
  the truth about a thing that does not constrain a dishonest one.

`evaluate_isolation` refuses with `no_isolation_evidence` when there are zero
probes, and the message names how many assertions and declarations it is
declining to accept — so the log says what was offered instead of evidence.

## The bypass

`allow_unisolated=True` is the local-development escape hatch, and it is not
honoured on its own: it requires a proof callable that actually returns True.
A flag that works because it was passed is a flag that works in production,
which is how development conveniences become incidents.

A bypassed run returns a record with `verified=False`. It is allowed and
honestly labelled — never recorded as verified, because the audit trail is the
one artifact that has to survive the convenience.

## Run it

```bash
cd apps/unproven-isolation-fails-closed
python -m unittest test_isolation.py -v
```

All ten tests use toy probes and assertions: passing probes, an assertion
alone, a declaration alone, both together, assertions surviving into the
record, a failing probe, an assertion failing to rescue it, the bypass flag
alone, the bypass with a proof that returns False and one that returns True,
and a bypassed run never being marked verified.

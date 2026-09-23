# permissive-contract-is-a-gap

**Atomic claim:** If a contract admits a value the instruction forbids, that is
a gap — recorded even when no artifact has ever sent such a value.

**Inspired by:** the CONTRACT GAP status in instruction-adherence evidence
registries (named for context; this app does not import or depend on any other
source). Tier 2, v1.5.

**Enforcement class:** deterministic — the contract is asked directly about
each forbidden value.

## The failure this catches

This is the most comfortable kind of failure. Every sample passes, every test
is green, and the only thing holding the line is that nobody has yet sent the
empty string the schema has always accepted.

The contract is what will be enforced tomorrow, against traffic nobody has seen
yet. Today's well-behaved artifacts are not evidence about it.

## How it works

A `Rule` is an instruction plus the values it forbids. `audit(contract, rules)`
asks the contract about each forbidden value and reports `enforced` or
`contract_gap`, naming the values that got through.

**Nothing else is consulted.** `audit` takes a contract and rules — there is
nowhere to pass a sample artifact, and a test asserts that signature, because
the moment real traffic enters the question it starts answering a different
one. There is a test where every real value passes the contract and the gap is
reported anyway.

A rule that forbids nothing is refused at construction. It cannot be violated,
so a contract cannot fail it, so declaring it proves nothing — the same
vacuity that [falsifiable-instruction-check](../falsifiable-instruction-check)
refuses on the checker side.

## Run it

```bash
cd apps/permissive-contract-is-a-gap
python -m unittest test_contract_gap.py -v
```

Ten tests over toy string schemas: a fully enforcing contract, one that admits
whitespace, the admitted values being named, no artifact in the signature, a
gap reported while all real traffic passes, several rules failing at once, a
rule that forbids nothing, an empty rule set, one finding per rule, and a type
check.

# authenticated-agent-message

**Atomic claim:** A message between agents is accepted only if it is signed by
a sender the recipient knows, addressed to that recipient, and carries a
sequence number strictly greater than the last one accepted from that sender.

**Inspired by:** authenticated inter-agent message contracts (named for
context; this app does not import or depend on any other source). Tier 3,
v1.4. Closes the ASI07 gap in [CONFORMANCE.md](../../CONFORMANCE.md).

**Enforcement class:** deterministic — HMAC verification plus exact identity
and sequence comparison.

## An envelope, not a bus

This app has no router, no queue, no delivery and no loop. PLAN.md places
multi-agent orchestration out of scope and that has not changed — but the risk
ASI07 describes is about the *message*, and a message contract is a primitive.
Building an envelope is not building a bus.

It answers one question a recipient must answer about one message it has
already received by some means: **is this from who it says, for me, and new.**

## How it works

`Recipient.accept(message)` runs four checks in a fixed order:

- **`unknown_sender`** — no key held for that sender.
- **`signature_invalid`** — the HMAC does not verify.
- **`misaddressed`** — signed, genuine, and addressed to someone else. Acting
  on it is the agentic equivalent of opening someone else's post.
- **`replayed`** — the sequence is not greater than the last accepted from
  that sender.

The signature covers **every field the recipient will act on** — sender,
recipient, sequence and payload — not just the payload. That is what makes the
`misaddressed` case safe: an intercepted message cannot be re-addressed to a
different agent and still verify. There is a test for exactly that, and it
fails as `signature_invalid` rather than `misaddressed`, because the
redirection broke the signature first.

Two decisions worth naming:

- **A gap in the sequence is accepted.** A missing message may have been
  dropped, and refusing to move past it would let one lost message wedge the
  channel permanently. What must never be accepted is a sequence already seen
  or older — that is a replay, and it is checked.
- **Each sender has its own sequence.** One chatty sender cannot invalidate
  another's messages.

## Run it

```bash
cd apps/authenticated-agent-message
python -m unittest test_agent_message.py -v
```

All eleven tests use toy agent identities and keys: an accepted message, an
unsigned one, a wrong-key signature, a payload edited after signing, a message
for another agent, an intercepted message re-addressed, a replay, an older
sequence, a gap, an unknown sender, and per-sender sequences.

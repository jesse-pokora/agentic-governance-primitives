# failure-bulkhead

**Atomic claim:** After a declared number of consecutive failures the breaker
opens and every subsequent call fails fast without invoking the dependency —
and it closes only when an explicit probe, allowed no earlier than a declared
cooldown, actually succeeds.

**Inspired by:** circuit-breaker and bulkhead patterns in distributed systems
(named for context; this app does not import or depend on any other source).
Tier 2, v1.4. Strengthens ASI08 coverage in
[CONFORMANCE.md](../../CONFORMANCE.md).

**Enforcement class:** deterministic — integer comparison against an injected
clock, so the time behaviour is exact rather than machine-speed dependent.

## How it works

The failure this prevents is not the first error. It is the thousandth. An
agent that keeps calling a dependency which is already down turns one broken
service into a queue of stuck runs, and **the retries are what carry the
failure outward** — which is what makes a cascade a cascade rather than an
outage.

`call(action)` invokes the dependency while the breaker is closed and counts
consecutive failures. At the threshold it opens; from then on `call` raises
`circuit_open` **without touching the dependency**. The test dependency counts
its own invocations, so "failed fast" is observable rather than asserted: fifty
calls against an open breaker leave the count unchanged.

Three decisions carry the claim:

- **Consecutive means consecutive.** One success clears the count. A breaker
  that accumulated failures forever would eventually open on a healthy
  dependency that had a bad minute last week.
- **The cooldown elapsing does not close the breaker.** Only a succeeding
  probe does. A breaker that closed on a timer would be deciding a service
  recovered without ever asking it — and would reopen on the next real call,
  having spent a real request to find out.
- **A failed probe restarts the cooldown.** Otherwise a down dependency gets
  probed on every call the moment the first cooldown passes, which is the
  hammering the breaker exists to stop.

This is not a retry policy. It never calls anything twice; it decides whether
to call at all. Pairs naturally with
[bounded-execution-budget](../bounded-execution-budget), which bounds how much
one run may consume, where this bounds how hard one dependency may be pushed.

## Run it

```bash
cd apps/failure-bulkhead
python -m unittest test_bulkhead.py -v
```

All ten tests use a fake clock and a dependency that counts invocations:
failures below threshold, the threshold opening it, fifty fast failures, a
success clearing the count, an early probe, a failing probe restarting the
cooldown, a succeeding probe closing it, the cooldown alone not closing it,
probing a closed breaker, and the transition history.

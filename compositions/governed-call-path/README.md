# governed-call-path

**Atomic claim:** One request passes through every declared gate in a fixed
order, and the first gate that refuses stops it — no later gate is entered, no
effect occurs, and the ledger records which gate refused.

**Composed from:** nine apps in [apps/](../../apps), imported unchanged —
`hash-pinned-instruction-set`, `optional-input-does-not-block`,
`declared-objective-conformance`, `bounded-execution-budget`,
`capability-gated-tool-invocation`, `pinned-egress-allowlist`,
`write-scope-confinement`, `managed-block-confinement` and
`authenticated-transition-ledger`.

## Why this is not in `apps/`

Every app in `apps/` is one atomic claim and imports nothing from its siblings.
This is the exception, so it lives somewhere else rather than quietly breaking
that rule.

It exists because **a control plane that nothing routes through is
documentation.** Forty-seven primitives demonstrated side by side still leave
the load-bearing claim — that they compose — untested. This is the smallest
artifact that tests it.

## Why this is not an orchestrator

`PLAN.md` puts orchestration out of scope and that has not changed. There is no
router: the order is a constant, `GATES`. No scheduler, no queue, no second
agent, no loop, no state machine. It is one request entering seven gates and
then doing one thing.

The distinction is the same one that let ASI07 be covered: a message bus is
orchestration, a signed envelope is a primitive. A workflow engine is
orchestration; one call path with a fixed gate order is a composition.

## What it demonstrates

```
instruction-set → intake → objective → budget → capability → egress → write-scope → effect
```

- **A compliant request passes all seven and writes its managed block.**
- **Each gate can refuse, and there is a test for each one** — drifted
  instructions, missing required intake, an undeclared objective, an exhausted
  budget, a missing capability, an unlisted egress host, an out-of-scope write.
- **A refusal stops everything after it.** `assert_stopped_at` checks that no
  gate later in the declared order was even entered, and a separate test
  confirms no file appears on disk for four different refusal points.
- **The ledger records refusals, not only successes.** A gate that logged only
  what it allowed would be useless exactly when it mattered, and the evidence
  of a refused run is tamper-evident too.

## Two things this got wrong first, which are worth knowing

**Verdict order is not gate order.** Three of these gates wrap the rest of the
path — the objective authorizes the action, the budget charges for it, the
capability gate admits the tool that performs it — so their verdicts complete
innermost-first, the way a call stack unwinds. The trace records the order
gates were *entered*, which is what a reader means by "the order of the gates".

**An inner refusal must not be attributed to the outer gate.** The budget gate
wraps the capability gate, so a capability refusal propagates through it. The
first version recorded that as the budget refusing, which names the wrong gate
in every nested case — which is the one question a reader actually has. Only
the gate that originates a refusal records it.

## A real limit

The budget and the objectives belong to the path, not to one request, because a
budget rebuilt per request bounds nothing — every request would start full.
That means this models **one run that handles several requests**. A design
where each request is its own run needs its own budget lifecycle, and that is a
decision, not a detail.

## Run it

```bash
cd compositions/governed-call-path
python -m unittest test_pipeline.py -v
```

All thirteen tests use real temp directories and the real modules: a compliant
request, the declared order, seven separate refusals, no effect on refusal, the
ledger recording every gate, a refusal appearing in the ledger, and the
refused run's evidence being tamper-evident.

# single-purpose-adversarial-reviewer

**Atomic claim:** One adversarial-review agent, schema-in/findings-out,
callable with zero pipeline, zero orchestrator, and no state carried
between calls.

**Inspired by:** single-purpose adversarial-review agents (named for
context; this app does not import or depend on that source).

**Enforcement class:** hybrid — the input/output envelope and
statelessness are deterministically enforced; the finding logic itself is
a deterministic toy stand-in for what would otherwise be generated
content from a model call.

## How it works

`review(payload)` is the module's only public function: it validates
`payload` against a fixed `{"artifact_id", "content"}` shape, runs a
toy rule-based scan (flagging `eval(` usage and password-like strings),
and returns `{"artifact_id", "findings": [...]}` where every finding has
exactly `{"severity", "description"}` with severity from a fixed
vocabulary.

There is no class, no module-level mutable state, and no orchestrator
calling it — `review()` is a pure function of its input. Calling it
repeatedly, or in different orders with different inputs, never changes
its output for a given input.

## Run it

```bash
cd apps/single-purpose-adversarial-reviewer
python -m unittest test_review_agent.py -v
```

One test inspects the module's own namespace to confirm `review` is the
only public callable it exposes — there is no hidden pipeline entry
point.

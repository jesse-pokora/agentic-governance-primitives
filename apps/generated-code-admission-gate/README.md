# generated-code-admission-gate

**Atomic claim:** Model-generated code is admitted only if every import, call,
and attribute access in its parsed AST is permitted by the declared policy — a
denied program is never compiled and never runs.

**Inspired by:** static review of agent-generated code before execution (named
for context; this app does not import or depend on any other source). Tier 1,
v1.2. Closes the one ASI05 gap in [CONFORMANCE.md](../../CONFORMANCE.md) that
was a missing primitive rather than a consequence of excluding orchestration.

**Enforcement class:** deterministic — AST inspection with exact name matching.
No regular expressions, no heuristics, no scoring.

## This is an admission gate, not a sandbox

It decides whether code is allowed to *start*. It does not contain code that is
already running. Restricted-namespace `exec` in CPython is known to be
escapable, and this app claims no isolation: real containment needs a process,
container, or VM boundary.

Saying so is the point. A gate that advertised itself as a sandbox would be the
most dangerous app in this catalog — it would be trusted for something it
cannot do. What is claimed, and tested, is narrow and true: a denied program
never reaches `compile`.

## How it works

`inspect_source(source, policy)` parses the source and walks the AST:

- **Imports** — the root module must be in `allowed_imports`.
- **Calls** — the callee must resolve to a plain dotted name (`record`,
  `math.sqrt`) that is in `allowed_calls`. A call the gate cannot resolve
  statically — through a subscript, a lambda, a returned object — is denied as
  `unresolvable_call` rather than assumed benign.
- **Forbidden names** — `eval`, `exec`, `compile`, `__import__`, `open`,
  `globals`, `getattr` and friends are refused **even when the policy
  allowlists them**. Each one turns a static check of the source into a check
  of source that no longer describes what will run; a policy that could
  re-enable them would be a policy that can disable itself.
- **Dunder access** — refused outright. `().__class__.__bases__[0].__subclasses__()`
  reaches every loaded class without importing anything, so the gate rejects
  the whole shape rather than enumerating which dunders are dangerous.

Violations are collected and the earliest in source order is reported; where
two land on the same position, the more specific reason wins. The same program
always produces the same denial.

Two properties separate this from the version everyone writes first:

- **It admits whole programs, not lines.** A `record()` call on line 1 does not
  run because line 2 imports something undeclared. Admission is all-or-nothing.
- **It parses instead of pattern-matching.** `banner = "import os and eval()
  are not allowed"` is an admissible program — it contains a string, not a call.
  A denylist grepping for `import os` or `eval(` rejects it, and the same
  denylist misses `__import__('os')` entirely. Both directions have tests.

At runtime, admitted code gets a restricted namespace plus a guarded importer
that honours the same allowlist the static pass used, so the runtime cannot
import what the gate would not have admitted.

## Run it

```bash
cd apps/generated-code-admission-gate
python -m unittest test_admission_gate.py -v
```

All eleven tests use toy generated sources and a spy that records whether
denied code ever executed: an admitted program, an allowed import, an
undeclared import, the `__import__` bypass, the dunder escape chain, `eval`
surviving an over-permissive policy, an undeclared call, an unresolvable call,
a forbidden name inside a string, unparseable source, and source-order
precedence.

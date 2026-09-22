# reduced-child-environment

**Atomic claim:** A child process receives only the variables a declared
policy passes through — every other variable in the parent's environment,
including ones nobody anticipated, is absent rather than redacted.

**Inspired by:** reduced-environment launch policies in governed agent hosts
(named for context; this app does not import or depend on any other source).
Tier 1, v1.3.

**Enforcement class:** deterministic — the child environment is constructed
from an allowlist, not filtered from the parent.

## How it works

The direction matters more than the list. `build_child_environment` starts
from `{}` and adds what the policy allows, rather than starting from the
parent and deleting what it forbids.

That is the whole claim. An allowlist is wrong only when it omits something
the child needed, and that failure is loud: the child breaks immediately and
somebody fixes the policy. A denylist is wrong the moment anyone adds a new
secret to the environment, and that failure is silent — the variable flows
through and nothing looks different. There is a test named for exactly this:
a variable called `SOME_FUTURE_SECRET` that no rule mentions is absent from
the child anyway.

Absent, not redacted: a variable that is not there cannot be read by anything
the child runs, including code the child shells out to later. A redacted value
is still a key in a map somebody can enumerate.

Two supporting decisions:

- **Platform essentials are declared, not assumed.** `PATH`, `SYSTEMROOT`,
  `TEMP` and friends pass through by default because a process needs them to
  start at all — but the list is written down in the module and can be
  declined entirely, so the default is visible rather than implicit.
- **An injected value colliding with a passthrough is refused.** Silently
  choosing one would make the child's environment depend on evaluation order.

The test suite launches a real child process that dumps its own environment as
JSON, and asserts the seeded secrets are not in the output — including one set
on this test process itself, to show the child is not inheriting by another
route.

## Run it

```bash
cd apps/reduced-child-environment
python -m unittest test_environment.py -v
```

All nine tests use toy secret values: a passthrough variable, seeded secrets
absent, an unanticipated secret absent, platform essentials, declining them,
injection, a colliding injection, a real child process, and no inheritance
from the test process.

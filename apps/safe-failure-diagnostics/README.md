# safe-failure-diagnostics

**Atomic claim:** A child-process failure is classified into one of a fixed
vocabulary of categories from at most 8,192 observed bytes, and only the
category — never the bytes — is ever persisted.

**Inspired by:** sanitized failure diagnostic capture (named for context;
this app does not import or depend on that source).

**Enforcement class:** deterministic — classification is marker-based
pattern matching over a bounded byte window with a fixed, closed set of
output categories.

## How it works

`classify_failure(raw_output)` inspects only `raw_output[:8192]`
(`MAX_INSPECTED_BYTES`) and matches it against a fixed set of markers,
returning one of `timeout`, `permission_denied`, `not_found`, `crash`, or
`unknown` — never a custom or open-ended category.

`persist_failure(raw_output)` is the only function that stands between
"bytes captured from a failed process" and "what gets written to storage":
it returns `{"category": ...}` and nothing else. The raw bytes are never
part of the return value, so a caller that only ever calls
`persist_failure` structurally cannot leak them.

## Run it

```bash
cd apps/safe-failure-diagnostics
python -m unittest test_diagnostics.py -v
```

One test plants a failure marker just past the 8,192-byte boundary to prove
the classifier genuinely stops reading there rather than scanning the whole
buffer.

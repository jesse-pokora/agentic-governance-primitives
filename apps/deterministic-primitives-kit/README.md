# deterministic-primitives-kit

**Atomic claim:** The same input byte-for-byte always produces the same
canonical JSON, the same hash, and the same safe-ID validation — across
restarts, across machines.

**Inspired by:** canonical-JSON / safe-ID / atomic-write primitives (named
for context; this app does not import or depend on that source).

**Enforcement class:** deterministic — every function is pure: no clock,
no randomness, no locale or environment dependence.

## How it works

- `canonical_json(obj)` serializes with sorted keys, no extraneous
  whitespace, and ASCII escaping, so logically-identical dicts built in
  different key order always produce identical output.
- `content_hash(obj)` is the SHA-256 of `canonical_json(obj)` — a stable
  fingerprint for any JSON-compatible value.
- `is_safe_id(value)` checks a fixed regex (`^[a-z0-9][a-z0-9_-]{0,63}$`),
  so the same string always gets the same true/false answer.

## Run it

```bash
cd apps/deterministic-primitives-kit
python -m unittest test_primitives.py -v
```

Tests hash the same toy payload 100 times and assert every result is
identical, and check that dicts built with keys in different orders still
hash to the same value.

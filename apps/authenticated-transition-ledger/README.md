# authenticated-transition-ledger

**Atomic claim:** An append-only, SHA-256-chained, HMAC-signed event log
detects a single edited byte anywhere in its history, not just at the
tampered row.

**Inspired by:** authenticated transition ledgers (named for context; this
app does not import or depend on that source).

**Enforcement class:** deterministic — chain, hash, and HMAC checks are
binary pass/fail.

## How it works

Each `LedgerEntry` stores `prev_hash` (the previous entry's `entry_hash`, or
a genesis constant for entry 0), a JSON `payload`, its own `entry_hash =
SHA256(prev_hash + canonical_json(payload))`, and an `hmac_sig` computed
over `(index, prev_hash, entry_hash)` with a secret key never exposed to
whoever might tamper with stored entries.

`verify()` walks every entry from index 0, recomputing the expected
`prev_hash`, `entry_hash`, and `hmac_sig` at each step. Editing a payload
anywhere in the chain — even far from the tail — breaks that entry's own
hash check. An attacker who also patches the hash to match still can't
forge the HMAC without the secret key.

## Run it

```bash
cd apps/authenticated-transition-ledger
python -m unittest test_ledger.py -v
```

Payload events (`"provision"`, `"deploy"`, `"rollback"` against fake service
names) are toy data — no real infrastructure or secrets are involved; the
"secret key" is a hardcoded test fixture.

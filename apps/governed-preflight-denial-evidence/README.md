# governed-preflight-denial-evidence

**Atomic claim:** When a precondition fails, the system emits a
fixed-shape, allowlisted-field denial record — never raw stderr, paths, or
secrets.

**Inspired by:** governed preflight denial audits (named for context; this
app does not import or depend on that source).

**Enforcement class:** deterministic — the record's key set is asserted
against a fixed allowlist every time one is built.

## How it works

`run_preflight(precondition_name, check_fn)` calls `check_fn`. If it raises
anything at all, the exception object — and whatever sensitive detail it
carries (a secret, a file path, a stack trace) — is discarded immediately.
Only a `DenialRecord` with exactly three allowlisted fields (`denied`,
`reason_code`, `precondition`) is produced, using a reason code from a
fixed vocabulary rather than the exception's own message.

`DenialRecord.to_dict()` asserts its key set equals `ALLOWED_FIELDS` before
returning, so the fixed shape is enforced at construction time, not just by
convention.

## Run it

```bash
cd apps/governed-preflight-denial-evidence
python -m unittest test_preflight.py -v
```

The failing checks raise exceptions containing a toy fake secret and file
path; the tests assert neither ever appears in the resulting record.

# verified-secret-redaction

**Atomic claim:** No registered secret can appear in an emitted artifact — the
emitter redacts by exact value across nested structures, then re-reads its own
serialized output and refuses to emit at all if any secret survived.

**Inspired by:** output redaction and egress control for credential material
in governed agent runtimes (named for context; this app does not import or
depend on any other source). This is a v1.1 gap-closure app:
[safe-failure-diagnostics](../safe-failure-diagnostics) and
[governed-preflight-denial-evidence](../governed-preflight-denial-evidence)
both protect the *failure* path, and nothing covered ordinary successful
output.

**Enforcement class:** deterministic — exact substring replacement plus a
post-serialization verification pass, no pattern guessing and no entropy
heuristics.

## How it works

`SecretRegistry(secrets, correlation_key)` holds the values that must never
reach an artifact. `redact(obj)` walks dicts, lists, tuples, strings, and
bytes, replacing every occurrence; `emit(obj)` redacts, serializes to
canonical JSON, and then calls `assert_clean` on the result before returning
it.

Four details are what the app is actually about:

- **The emitter doesn't trust its own redactor.** `assert_clean` re-scans the
  finished bytes. That pass is the reason `emit` is safe against output that
  reached it through some other path — a structure built elsewhere, a type the
  walker doesn't know, a future edit to `redact`.
- **The failure message doesn't leak what it caught.** A `RedactionFailure`
  names only the placeholder. An exception that quoted the surviving secret
  would just be one more place the secret appears — usually in a log.
- **Placeholders are HMACs, and the key is required.** The same secret yields
  the same placeholder, so redacted logs still correlate across lines and
  runs; without the key, a placeholder reveals nothing. There is no default
  key, because a silent per-process default would break correlation across
  runs without anyone noticing.
- **Longest secret first.** When one secret contains another, replacing the
  shorter one first leaves a mangled fragment of the longer one in the output.
  Sorting by length is the whole fix, and it has its own test.

Dict keys are redacted alongside values: a secret used as a key is exactly as
exposed as one used as a value. A secret shorter than `MIN_SECRET_LENGTH` (4)
is rejected at registration — it would match inside ordinary words and shred
the document instead of redacting it.

## Run it

```bash
cd apps/verified-secret-redaction
python -m unittest test_redaction.py -v
```

All twelve tests use toy token strings (no real credential): nested values,
embedded substrings, dict keys, lists and bytes, placeholder stability,
overlapping secrets, the verification pass firing, the failure message staying
clean, end-to-end `emit`, non-string passthrough, and both registration
rejections.

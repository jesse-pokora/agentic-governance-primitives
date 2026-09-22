# pinned-egress-allowlist

**Atomic claim:** An outbound request is allowed only if its scheme, host, and
port all match an allowlist entry exactly — and every hop of a redirect chain
is checked, not just the first.

**Inspired by:** network egress allowlisting in sandboxed agent runtimes
(named for context; this app does not import or depend on any other source).
This is a v1.1 gap-closure app:
[hash-pinned-identity](../hash-pinned-identity) pins *what binary* runs, and
nothing pinned *where it may talk*.

**Enforcement class:** deterministic — exact tuple match on
(scheme, host, port) after a documented normalization, no suffix matching, no
wildcards.

## How it works

`PinnedEgressAllowlist(["https://api.example.test", ...])` parses each entry
into a frozen `EgressRule(scheme, host, port)`, filling in the default port
for the scheme. `check(url)` runs five checks in a fixed order — malformed,
scheme, host present, userinfo, port — so the same URL always produces the
same denial reason.

The interesting part is what "match" has to exclude:

- **Suffix lookalikes.** `api.example.test.evil.test` contains the allowlisted
  name and is a different host. Matching is on the whole hostname, never a
  prefix or suffix test.
- **Userinfo disguises.** In `https://api.example.test@evil.test/` the host is
  `evil.test`; the allowlisted name is just decoration before the `@`.
  Credentials in a URL are denied outright — they both leak and confuse.
- **IP literals.** An address that resolves to an allowlisted name is still not
  that name, and is denied.
- **Case and the root dot.** DNS is case-insensitive and `example.test.` names
  the same host as `example.test`, so both are normalized *toward* the
  allowlist. Skipping this would let an exact-match allowlist be bypassed by
  typing the name differently.
- **Ports.** The implicit and explicit default port are the same target; an
  unlisted port on an allowlisted host is denied.
- **Schemes.** `file:///etc/...` is denied as `scheme_not_allowed`, checked
  before the host so a hostless URL is denied for the reason that actually
  disqualifies it.

`check_chain([...])` applies all of that to every hop. The denial keeps the
failing hop's own precise reason and names the hop index, so a 302 into an
exfiltration host reads as `host_not_allowed` at `hop=1` rather than as a
generic redirect failure.

## Run it

```bash
cd apps/pinned-egress-allowlist
python -m unittest test_egress.py -v
```

All eleven tests are pure string/URL checks against `.test` reserved names —
nothing resolves DNS and no socket is ever opened.

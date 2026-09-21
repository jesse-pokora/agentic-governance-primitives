# hash-pinned-identity

**Atomic claim:** A launcher refuses to run any executable whose resolved
absolute path *and* SHA-256 don't both match a policy pinned outside the
workspace — even if the name on `PATH` is identical.

**Inspired by:** hash-pinned execution identity policies in governed agent
launchers (named for context; this app does not import or depend on that
source).

**Enforcement class:** deterministic — binary pass/fail on path equality and
hash equality, no fuzzy matching, no fallback.

## How it works

`PinnedIdentityPolicy` maps a logical executable name to a `PinnedIdentity`
(absolute path + SHA-256), standing in for a policy file kept outside the
workspace an agent can write to. `HashPinnedLauncher.launch(name,
candidate_path)` only returns the executable's bytes if **both**:

1. `candidate_path` resolves to the exact pinned absolute path, and
2. the SHA-256 of the file at that path matches the pinned hash.

Any other case — a same-named impostor earlier on `PATH`, a tampered file at
the correct path, or an unregistered name — raises `IdentityMismatch` with a
fixed-vocabulary reason (`path_mismatch`, `hash_mismatch`, `missing_file`, or
`no pinned identity`).

## Run it

```bash
cd apps/hash-pinned-identity
python -m unittest test_launcher.py -v
```

All four tests are toy scenarios (temp-directory fixtures, no real binaries
or credentials): an exact match, a `PATH`-hijack impostor, tampered content
at the trusted path, and an unregistered name.

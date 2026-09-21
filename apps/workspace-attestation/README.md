# workspace-attestation

**Atomic claim:** A governed run's *claimed* file changes are diffed
against a real git-worktree snapshot taken immediately before and after —
a claim that doesn't match the diff fails closed.

**Inspired by:** workspace attestation around agent-driven test runs
(named for context; this app does not import or depend on that source).

**Enforcement class:** deterministic — the claimed change-set either
equals the actual `git status` diff or the attestation raises.

## How it works

`init_snapshot_repo(repo_dir)` runs a real `git init` + commit of the
directory's current contents — the "before" snapshot. After a run makes
its changes, `capture_actual_diff(repo_dir)` runs real `git status
--porcelain=v1` against that commit and parses it into added/modified/
deleted file sets — this is the real git-worktree diff, not a
self-reported one.

`attest(repo_dir, claimed_added, claimed_modified, claimed_deleted)`
compares the claim to that actual diff. Any discrepancy — a change the
claim omits, or one it invents — raises `AttestationMismatch` carrying both
the claimed and actual sets, and nothing is treated as attested.

Every git command runs with `-c user.name=... -c user.email=...` flags
scoped to that single invocation, so this app never touches any real git
config.

## Run it

```bash
cd apps/workspace-attestation
python -m unittest test_attestation.py -v
```

Requires `git` on `PATH`. Each test runs against a throwaway temp-directory
repo with toy file contents — nothing touches this repository itself.

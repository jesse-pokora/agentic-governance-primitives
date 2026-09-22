# staged-input-allowlist

**Atomic claim:** Only files matching the declared policy enter the agent's
view, every excluded file is recorded with a fixed-vocabulary reason, and
exceeding a declared cap stages nothing at all.

**Inspired by:** staging-policy filters in governed agent hosts (named for
context; this app does not import or depend on any other source). Tier 1,
v1.3.

**Enforcement class:** deterministic — suffix, name, size and path-component
checks on the real filesystem.

## How it works

This is the input-side counterpart to
[write-scope-confinement](../write-scope-confinement): that app governs where
an agent may write, this one governs what it may ever see.

`stage(source, dest, policy)` walks the source tree and sorts every file into
staged or excluded. Exclusion reasons come from a fixed vocabulary —
`suffix_not_allowed`, `denied_name`, `too_large`, `symlink`, `vcs_metadata` —
and there is a test asserting that the staged set plus the excluded set equals
the source set exactly. **Nothing is dropped without a reason**, which is the
property that makes a staging policy reviewable: you can ask why any given
file is not in the agent's view and get an answer.

Two decisions carry most of the weight:

- **Caps refuse rather than truncate.** Exceeding the file-count or total-byte
  cap raises, and nothing is copied. Truncating to the cap would hand the
  agent a silently partial view of the repository — the worst available
  outcome, because nothing would look wrong and the guide it produced would be
  confidently incomplete.
- **Symlinks are excluded, not followed.** A link is a path into somewhere the
  policy never examined, so following it stages a file that was never
  classified.

Allowlisted suffixes and denied names are both declared, because they answer
different questions: the suffix list says what kind of file is useful, and the
denied-name list says what must never be staged even when its suffix is
allowed — `.env` and `id_rsa` are refused by name.

## Run it

```bash
cd apps/staged-input-allowlist
python -m unittest test_staging.py -v
```

All ten tests run against real temp directories: allowlisted staging, secret
filenames, an unlisted suffix, VCS metadata, an oversized file, a symlink,
full accounting of every source file, the manifest matching the staged set,
and both caps refusing without staging anything. The symlink test skips itself
where the platform or account cannot create symlinks.

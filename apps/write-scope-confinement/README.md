# write-scope-confinement

**Atomic claim:** A write is denied before any bytes touch disk unless its
fully resolved path lies inside the declared scope root — parent traversal,
absolute-path substitution, a sibling directory sharing a name prefix, and a
symlink inside the scope pointing outside it all fail closed.

**Inspired by:** filesystem confinement in sandboxed agent runtimes (named for
context; this app does not import or depend on any other source). This is a
v1.1 gap-closure app: [workspace-attestation](../workspace-attestation)
detects a claim that doesn't match the diff *after* the run, and nothing
prevented the out-of-scope write in the first place.

**Enforcement class:** deterministic — component-wise containment against one
realpath'd root, on the real filesystem.

## How it works

`ConfinedWriter(scope_root)` realpaths the root once and requires it to exist.
`resolve(path)` computes two paths and compares both against the root:

- `os.path.abspath(joined)` — the *lexical* path, with `..` normalized but no
  symlinks followed.
- `os.path.realpath(joined)` — the path bytes would actually land on.

That pair is what makes the denial reasons precise: a path already outside the
root is `traversal_escape` or `outside_scope`, while a path that *looks*
inside but resolves outside is `symlink_escape`. Containment itself uses
`os.path.commonpath` on normcased paths, not `startswith`, because
`<root>-evil` shares every character of the root's name and is a different
directory — the single most common way this check is written wrong.

`write(path, data)` resolves first and only then creates parent directories
and opens the file, so a denied write leaves no file, no partial file, and no
freshly created directories on the way.

## Run it

```bash
cd apps/write-scope-confinement
python -m unittest test_confined_writer.py -v
```

All eight tests run against real temp directories (no fake filesystem): an
in-scope write, `..` traversal, an absolute path outside, the prefix-sibling
directory, a symlink escape, the scope root itself, an empty path, and a
denied write leaving nothing behind. The symlink test skips itself when the
platform or account can't create symlinks — on Windows that needs Developer
Mode or an elevated shell.

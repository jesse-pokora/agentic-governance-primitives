# managed-block-confinement

**Atomic claim:** A managed write replaces only the content between the exact
markers — everything outside them survives byte for byte, and generated
content carrying a marker of its own is refused rather than written.

**Inspired by:** managed-block write discipline in governed documentation
agents (named for context; this app does not import or depend on any other
source). Tier 1, v1.3.

**Enforcement class:** deterministic — exact marker matching and string
slicing, on the real filesystem.

## How it works

`render_managed(document, content)` is pure: it returns the new document text
or raises, and never touches the disk. `write_managed_block(path, content)`
renders first and only then writes, so a refused write cannot leave a
partially updated file behind.

Four decisions carry the claim:

- **Outside the markers is not the agent's to touch.** The result is built by
  slicing the original document around the block, so the bytes before and
  after are the original bytes — CRLF endings, trailing spaces, tabs and all.
  Those are exactly what a careless rewrite-the-whole-file approach silently
  normalizes away, and there is a test for it.
- **Generated content carrying a marker is refused.** A model that emits
  `<!-- BEGIN MANAGED BLOCK -->` inside its own output would produce a
  document with two start markers, and every later edit would have to guess
  which region it owns. Refusing at render time means the file is never
  opened.
- **Ambiguity fails closed, absence does not.** No block at all is a legal
  state — it has not been created yet, and creating it appends without moving
  anything that was already there. Two starts, an unpaired marker, or an end
  before a start all refuse, because any answer would be a guess.
- **The replacement is indivisible.** `atomic_write` writes a temporary file
  in the same directory and calls `os.replace`, so a reader sees either the
  old document or the new one. That is the honest scope: it makes one file's
  replacement atomic. It does not make a multi-file operation transactional,
  and it does not claim to.

Writing the same content twice produces the same document and still exactly
one block, so a re-run is a no-op rather than a slow accumulation of blocks.

## Run it

```bash
cd apps/managed-block-confinement
python -m unittest test_managed_block.py -v
```

All eleven tests run against real temp files: replacing a block, byte-for-byte
preservation of CRLF and trailing whitespace outside it, first-time creation,
start-marker and end-marker injection, duplicate markers, an unpaired marker,
an inverted pair, a refused render leaving the file untouched, no temporary
file left behind, and idempotence.

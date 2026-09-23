# traceable-instruction-source

**Atomic claim:** An instruction is bound to the exact text at an exact
location; if the source no longer contains that text, resolving it is refused
rather than silently re-read from whatever now sits at those lines.

**Inspired by:** source-traceability requirements in instruction-adherence
registries (named for context; this app does not import or depend on any other
source). Tier 2, v1.5.

**Enforcement class:** deterministic — exact text comparison plus SHA-256.

## The trap this closes

Line numbers alone. Insert a paragraph above an instruction and every anchor
below it now points at somebody else's words — while still resolving cleanly,
still returning text, and still looking perfectly traceable. The criterion id
and the citation both survive; only the meaning changes.

Quoting the text and hashing it turns that from invisible drift into a
refusal. There is a test named for exactly that case.

## How it works

`anchor(sources, path, start, end)` records the path, the line range, the
quoted text and its digest. `resolve(anchor, sources)` returns the instruction
only when the text at those lines is still byte-identical:

- **`text_changed`** — the lines now hold something else, whether because the
  instruction was edited or because content moved above it.
- **`digest_mismatch`** — the quote matched but the recorded digest did not, so
  the anchor itself was tampered with rather than the source.
- **`range_out_of_bounds`**, **`source_missing`**, **`invalid_range`** — the
  location no longer exists.

Comparison is exact, so trailing whitespace counts as a change. That is the
same decision
[grounded-claim-verification](../grounded-claim-verification) makes for quotes:
an exact gate can be loosened deliberately, a fuzzy one cannot be tightened
back with confidence.

Edits elsewhere in the file do not invalidate an anchor, and there is a test
for that too — a rule that cried wolf on every unrelated change would be
switched off.

## Run it

```bash
cd apps/traceable-instruction-source
python -m unittest test_anchor.py -v
```

Eleven tests over a toy instruction file: unchanged source, an edited
instruction, a line inserted above, a whitespace-only change, truncation, a
missing file, a tampered digest, three invalid ranges, digest provenance,
two anchors agreeing, and an unrelated edit elsewhere.

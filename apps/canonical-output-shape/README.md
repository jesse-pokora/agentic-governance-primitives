# canonical-output-shape

**Atomic claim:** Generated output is accepted only if its headings are
canonical, spelled exactly and in the declared order, with no wrapper fence,
no empty section, and no more than the declared word bound — and the checker
never repairs what it rejects.

**Inspired by:** output-contract criteria for generated documentation (named
for context; this app does not import or depend on any other source). Tier 2,
v1.3.

**Enforcement class:** deterministic — exact string and order comparison.

## How it works

`verify_shape(document)` accepts or raises with the first violated rule:
`empty_output`, `wrapped_in_fence`, `malformed_heading`, `missing_title`,
`non_canonical_heading`, `headings_out_of_order`, `duplicate_heading`,
`empty_section`, `too_long`.

**Shape is checked, never repaired.** A validator that silently fixes its
input stops being able to tell you the generator is drifting — the drift moves
into the validator's patches, where nothing measures it, and the model's
output quietly gets worse while every run reports success.

Three cases are sharper than they look:

- **Omitting a section is fine; an empty heading is not.** A section the
  evidence did not support should be absent. A heading with nothing under it
  reads as an answer and is not one.
- **A malformed heading is not a heading.** `##Key Paths`, with no space, is
  not an ATX heading — Markdown renders it as body text. It would sail past a
  canonical-heading check while looking to a human like a section that is
  present. Catching it required a lookahead in the pattern, because a greedy
  `#{1,6}` happily matches `## Purpose` by treating the second `#` as the
  non-space character.
- **A fence inside a section is content; a fence around the document is a
  wrapper.** Only the second is rejected, so a Build and Test section can
  contain a shell block.

## Run it

```bash
cd apps/canonical-output-shape
python -m unittest test_output_shape.py -v
```

All twelve tests use toy documents: a conforming document, an omitted optional
section, an empty heading, four near-miss spellings, sections out of order, a
repeated heading, a wrapped document, a fenced block inside a section, a
missing title, exceeding the word bound, empty output, and the checker leaving
its input untouched.

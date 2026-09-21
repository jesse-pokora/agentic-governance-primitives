# governed-context-provenance

**Atomic claim:** Every piece of context handed to a model carries its
source and an explicit `injection_disposition` ("clear" vs. untrusted)
*before* assembly — the model never has to guess what it can trust.

**Inspired by:** provenance-tagged, request-scoped context assembly
(named for context; this app does not import or depend on that source).

**Enforcement class:** deterministic — assembly either has a valid
source and disposition for every item or it raises; there's no partial or
best-effort assembly.

## How it works

`assemble_context(items)` walks each context item and requires a
non-empty `source` string and an `injection_disposition` from the fixed
set `{"clear", "untrusted"}`. Any item missing either raises
`ProvenanceMissing` — the whole assembly fails closed rather than
silently dropping or under-tagging the bad item.

Every surviving block is rendered with an explicit
`[source=... disposition=...]` marker ahead of its content, so a model
reading the assembled prompt is told, not left to infer, which parts came
from where and whether they should be trusted.

## Run it

```bash
cd apps/governed-context-provenance
python -m unittest test_context_assembly.py -v
```

Context items (`"system-prompt"`, `"web-search-result-3"`) are toy
placeholders standing in for real context sources.

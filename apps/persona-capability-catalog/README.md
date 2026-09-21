# persona-capability-catalog

**Atomic claim:** "Who is allowed to do what" (a YAML+JSON-Schema catalog)
is fully separate from "what's running right now" (a runtime process
list) — you can audit the first without touching the second.

**Inspired by:** declarative persona/agent catalogs (named for context;
this app does not import or depend on that source).

**Enforcement class:** informational — there's no gate here, just a
pattern worth knowing; the tests instead verify the *separation* itself.

## How it works

`catalog.yaml` + `schema.json` declare personas and their allowed
capabilities from a fixed vocabulary. `catalog.py` loads and validates
that catalog. `runtime.py` is a toy in-memory process list standing in for
"what's actually executing right now." Neither module imports the other —
verified both statically (parsing each file's AST for cross-imports) and
dynamically (auditing the catalog never causes `runtime` to appear in
`sys.modules`, and vice versa).

That separation is the point: a security reviewer can audit *who is
authorized to do what* purely by reading the catalog, with zero risk of
that audit being entangled with, or dependent on, live process state.

## Run it

```bash
cd apps/persona-capability-catalog
pip install -r requirements.txt
python -m unittest test_catalog.py -v
```

This is the one app in the catalog with external dependencies
(`pyyaml`, `jsonschema`) — scoped to this directory only, since the
atomic claim specifically names a YAML+JSON-Schema catalog.

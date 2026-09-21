# prompt-injection-scanner-mcp

**Atomic claim:** A single-purpose MCP server that does exactly one thing
(flag likely prompt injection in a text blob) and nothing else.

**Inspired by:** single-purpose prompt-injection-scanning MCP servers
(named for context; this app does not import or depend on that source).

**Enforcement class:** hybrid — the single-tool surface is deterministic;
the marker list itself is a simple, non-exhaustive heuristic rather than a
comprehensive detector.

## How it works

`PromptInjectionScannerServer` models an MCP server's tool-registry shape
without a full JSON-RPC transport: `list_tools()` always returns exactly
`["flag_prompt_injection"]`, and `call_tool(name, arguments)` dispatches to
it or raises `UnknownTool` for anything else. The tool itself does simple
case-insensitive substring matching against a fixed list of known
injection phrases (`"ignore previous instructions"`,
`"reveal your system prompt"`, etc.) and returns
`{"likely_injection": bool, "matched_markers": [...]}`.

The "and nothing else" half of the claim is checked directly: a test
enumerates the class's public methods and asserts they are exactly
`list_tools` and `call_tool` — there is no second capability hiding behind
another name.

## Run it

```bash
cd apps/prompt-injection-scanner-mcp
python -m unittest test_scanner_server.py -v
```

This is a toy heuristic for teaching the single-purpose-server shape, not
a production-grade injection detector.

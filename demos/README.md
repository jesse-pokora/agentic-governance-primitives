# Demo pages

Every app in [apps/](../apps) ships an animated web page demonstrating its
atomic claim: `apps/<app>/demo.html`. Open one in a browser — no server, no
network, no build step.

## The one rule

**A demo page contains no app logic.** It is a view over a trace that was
produced by running the app's real Python module.

That constraint is the whole point. A page that reimplemented its app's logic
in JavaScript would be a *second* implementation, free to drift from the one
the tests cover — and the failure mode is the worst possible one: a green,
convincing page demonstrating a guarantee the shipped code no longer provides.

So the pipeline is:

```
apps/<app>/demo.py      calls the real module, records what happened
        |
        v
apps/<app>/demo.json    the recording: inputs, verdicts, denial reasons
        |
        v  demos/render.py + demos/template.html
        v
apps/<app>/demo.html    self-contained page, animates the recording
```

The recorder enforces this rather than trusting it. `Trace.deny()` raises if
the app *fails* to refuse the call it was told to refuse, so a demo cannot
quietly record an allow where its script promised a deny.

## Running things

```bash
cd apps/<app> && python demo.py     # re-record one app
python demos/render.py              # re-render every page
python demos/render.py apps/<app>   # re-render one

npm install && npx playwright install chromium   # once
npx playwright test                              # check every page
```

## What the Playwright suite checks

`demos.spec.js` loads each page and asserts it has not drifted from its
recording: the claim text, the step count, and for every step the verdict and
the exact denial reason the module raised. It also checks that the verdict
animates rather than appearing pre-rendered, that navigation bounds hold at
both ends, and that the page makes **no network requests at all**.

This is what makes a page a verified artifact rather than a picture of one.

## Diagrams

An app may have a diagram at `demos/diagrams/<app>.svg`, inlined into its page
above the steps. Five do, and they exist because the same mechanism was being
reassembled from prose on every read:

| App | What the picture shows |
|---|---|
| `write-scope-confinement` | The scope is a subtree; `work-evil` is a sibling that shares every character of `work` |
| `pinned-egress-allowlist` | The same error in the DNS tree: appending `.evil.test` keeps the text and changes the branch |
| `delegation-scope-attenuation` | Capability sets as a lattice, with the chain descending and amplification pointing back up |
| `bounded-execution-budget` | The declared limits as a region, the run as a staircase, and the step that leaves it refused whole |
| `concurrent-append-integrity` | A chain is a line; two writers naming the same predecessor make it a fork |

The first two are deliberately the same drawing in two domains, because the
underlying bug — a string prefix standing in for a path in a tree — is the most
repeated defect in the catalog and is invisible until you see it twice.

A diagram is **authored, not recorded**. It shows the mechanism the claim is
about, which no trace can express, so it is a file rather than something
`demo.py` produces. It is inlined rather than linked so the page stays
self-contained, and it draws in `currentColor` and the page's own `--deny`
variable so it reads in both themes.

Playwright checks each one: inline, `role="img"` with a real `aria-label`, a
non-empty caption, no external reference, and a sane size in dark mode.

## Recordings are byte-stable

Re-running every `demo.py` produces byte-identical `demo.json` files, so a
recording can be committed, diffed in review, and regenerated to prove the
page still matches the code. Where a value is genuinely volatile — a temp
directory, a freshly minted challenge — the demo declares it in
`Trace.redactions` and it is replaced with a stable placeholder. That
normalizes how a value is *shown*; it never changes an outcome, a reason, or
whether a call was allowed.

## Adding a demo

```python
def build() -> Trace:
    t = Trace(app="...", claim="...", enforcement="deterministic",
              denial_type="WhateverDenied")
    t.allow("label", {"shown": "input"}, lambda: thing.do(ok), evidence=lambda: "...")
    t.deny("label", {"shown": "input"}, lambda: thing.do(bad), note="why this matters")
    return t
```

`t.verdict(...)` is for apps that report pass/fail by return value rather than
by raising — `ledger.verify()` and friends.

Prefer steps that show the *near misses*: the case a looser implementation
would wave through. A demo of the happy path proves almost nothing.

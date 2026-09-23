# Method

How an app in this catalog is written, and how to tell whether a new one is
scoped right. This is the part that transfers: the 47 apps are worked examples
of these four conventions.

## 1. One atomic claim

Every app states one sentence a skeptic could test, in its README and in
[claims.json](claims.json).

**The tell for a mis-scoped app is an "and" joining two rules.** If the claim
needs one, it is two apps. That test found the split between
[attested-rollback-checkpoint](apps/attested-rollback-checkpoint) — restore only
a digest that was attested — and
[forward-only-revert-journal](apps/forward-only-revert-journal) — never erase
history. Either can hold without the other, so they are two claims.

Not every "and" is fatal. An "and" listing cases the *same* rule covers is
fine: "traversal, absolute paths, prefix siblings and symlink escapes all fail
closed" is one rule with four shapes. An "and" joining two things that could be
independently true or false is the problem.

The rule cuts only one way — it catches apps that should be split, never apps
that should be merged. That needs a deliberate pass; see the overlap review in
[PLAN.md](PLAN.md).

## 2. One case per enumerated item, per surface

When a claim enumerates things — file types, forbidden names, resource kinds,
denial reasons — the tests carry **one case for each enumerated item, on each
surface where it applies.** Not one case that happens to exercise three of
them, and not a loop asserting a property in aggregate.

The reason is diagnostic, not ceremonial. A test named for the item it covers
tells you which item broke; a test over a collection tells you the collection
broke. When
[staged-input-allowlist](apps/staged-input-allowlist) refuses five kinds of
file, there are five named tests, plus one asserting that the staged and
excluded sets together account for every source file — the aggregate check
earns its place by proving nothing was dropped *silently*, which no per-item
test can.

Where a criterion appears in more than one place, score it once and record the
other locations as aliases rather than as extra weight.

## 3. Enforcement class

Declared per app, and it is a statement about what the app can promise:

- **deterministic** — binary pass/fail on exact comparison. No heuristics, no
  scoring, no model in the loop.
- **hybrid** — a deterministic envelope around generated content. The envelope
  is checkable; what it contains is not.
- **informational** — a pattern worth knowing that gates nothing, and it says
  so in its first paragraph.

An app that would like to be deterministic but is not must say so rather than
rounding up. [prompt-injection-scanner-mcp](apps/prompt-injection-scanner-mcp)
is hybrid because flagging is advisory; calling it deterministic would be a
claim about catching every injection that nobody can make.

## 4. Criticality

Not every control matters equally, and a catalog that pretends otherwise
cannot answer "if I only implement five, which five?"

| Tier | What a violation means |
|---|---|
| **C0** | Unauthorized action becomes possible, or the evidence of one is destroyed. Fail closed, no exceptions, no degraded mode. |
| **C1** | Governance degrades, or a fact an auditor needs is hidden. The system still refuses the right things; it stops being able to prove it. |
| **C2** | Correctness or predictability suffers, but authority is intact. |
| **C3** | A convention whose violation costs clarity. |

How the catalog currently distributes across both, generated from
`claims.json`:

<!-- BEGIN MANAGED BLOCK -->
| Enforcement | Apps | | Criticality | Apps |
|---|---|---|---|---|
| deterministic | 55 of 59 | C0 | 20 of 59 |
| hybrid | 3 of 59 | C1 | 23 of 59 |
| informational | 1 of 59 | C2 | 14 of 59 |
| | | C3 | 2 of 59 |
<!-- END MANAGED BLOCK -->

Criticality is about the **consequence of the control being absent**, not about
how likely the failure is or how hard the app was to write. Two consequences
put an app in C0: something becomes possible that should not be, or something
that happened stops being provable.

## Adding an app

1. Write the claim first, in one sentence. If it needs an "and", stop and split.
2. Build the module: standard library only unless there is no alternative, no
   imports from sibling apps, fixed-vocabulary denial reasons.
3. Write tests covering the happy path, each enumerated case, and the near
   misses a looser implementation would wave through. The near misses are the
   point — a demo of the happy path proves almost nothing.
4. Write `demo.py` recording the real module (see [demos/](demos)) and
   regenerate the page.
5. Add the authored fields to `claims.json`: tier, release, criticality, and
   the standards mapping. `python tools/sync_claims.py` will tell you which are
   missing and fill in the rest from the recording.
6. `python run_all.py --demos` and `python tools/generate_docs.py`.

## What this catalog does not claim

Each app demonstrates that a control **can** be enforced deterministically,
with a test that runs in seconds. None of them is a production control, and
running them proves nothing about any system that has not adopted them. The
mapping in [CONFORMANCE.md](CONFORMANCE.md) is an interpretive one, and
"covered" there means *one control demonstrated*, never *the risk handled*.

# telemetry-is-not-cost

**Atomic claim:** A token count becomes a monetary figure only against a pinned
rate card for that exact model and version — and two amounts in different
currencies will not add.

**Inspired by:** the rule that token telemetry is not monetary cost (named for
context; this app does not import or depend on any other source). Tier 5,
v1.5.

**Enforcement class:** deterministic — exact model and currency matching over
`Decimal` arithmetic.

## Why this keeps happening

Token counts get quoted as money because they are the number that happens to be
in the log. They measure work, not spend: the rate changes over time, differs
per model, differs between input and output, and is not knowable from the count
at all.

`Usage` therefore has **no cost method and no currency**. There is a test
asserting that, because the cheapest way to prevent the mistake is to make the
type unable to express it.

## How it works

`cost(usage, card)` refuses four ways:

- **`no_rate_card`** — the conversion has no basis.
- **`rate_card_mismatch`** — the card is for a different model *or a different
  version of the same model*. Applying last quarter's card is a guess wearing a
  decimal point.
- **`invalid_usage`** — negative tokens.
- plus **`currency_mismatch`** when adding, because summing across currencies
  needs an exchange rate, which is another pinned fact nobody supplied.

Input and output are priced separately, and `Decimal` is used throughout: a
per-token rate in binary floating point accumulates error in exactly the
direction nobody checks.

Pairs with
[measured-token-accounting](../measured-token-accounting), which establishes
that the count is real. This one establishes that the count is not dollars.

## Run it

```bash
cd apps/telemetry-is-not-cost
python -m unittest test_rate_card.py -v
```

Twelve tests over a toy rate card: a matching conversion, no card, usage having
no cost method, a card for another model, a card for another version, input
priced apart from output, amounts adding, currencies refusing to add, a card
with no currency, a negative rate, negative usage, and totalling nothing.

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from rate_card import Money, RateCard, Usage, cost, total  # noqa: E402

USAGE = Usage("toy-model", "2026-01-01", input_tokens=10_000, output_tokens=2_000)
CARD = RateCard("toy-model", "2026-01-01", "USD",
                Decimal("0.003"), Decimal("0.015"), "2026-01-01")
CARD_TEXT = "toy-model 2026-01-01, USD, 0.003/1k in, 0.015/1k out"


def build() -> Trace:
    t = Trace(
        app="telemetry-is-not-cost",
        claim=(
            "A token count becomes a monetary figure only against a pinned rate card "
            "for that exact model and version — and two amounts in different "
            "currencies will not add."
        ),
        enforcement="deterministic",
        denial_type="CostRefused",
    )
    t.allow("usage priced against a matching card",
            {"usage": "10,000 in / 2,000 out, toy-model 2026-01-01",
             "rate card": CARD_TEXT},
            lambda: f"{cost(USAGE, CARD).amount} {cost(USAGE, CARD).currency}",
            evidence=lambda: "input and output priced separately")
    t.deny("the same usage, reported as money with no card",
           {"usage": "10,000 in / 2,000 out", "rate card": "(none)"},
           lambda: cost(USAGE, None),
           evidence=lambda: f"Usage has a cost method: {hasattr(USAGE, 'cost')}; "
                            f"a currency: {hasattr(USAGE, 'currency')}",
           note="Token counts get quoted as money because they are the number in the "
                "log. The type is built so it cannot express the claim.")
    t.deny("a card for a different model",
           {"usage": "toy-model 2026-01-01", "card": "other-model 2026-01-01"},
           lambda: cost(USAGE, RateCard("other-model", "2026-01-01", "USD",
                                        Decimal("0.001"), Decimal("0.002"), "2026-01-01")))
    t.deny("a card for a later version of the same model",
           {"usage": "toy-model 2026-01-01", "card": "toy-model 2026-06-01"},
           lambda: cost(USAGE, RateCard("toy-model", "2026-06-01", "USD",
                                        Decimal("0.004"), Decimal("0.020"), "2026-06-01")),
           note="Applying last quarter's card is a guess wearing a decimal point.")
    t.allow("two amounts in the same currency",
            {"a": "0.060 USD", "b": "0.060 USD"},
            lambda: f"{total(cost(USAGE, CARD), cost(USAGE, CARD)).amount} USD")
    t.deny("two amounts in different currencies",
           {"a": "1.00 USD", "b": "1.00 EUR"},
           lambda: total(Money(Decimal("1.00"), "USD"), Money(Decimal("1.00"), "EUR")),
           note="Summing across currencies needs an exchange rate, which is another "
                "pinned fact nobody supplied.")
    t.deny("a rate card with no currency",
           {"model": "toy-model", "currency": "(empty)"},
           lambda: RateCard("toy-model", "2026-01-01", "", Decimal("0.003"),
                            Decimal("0.015"), "2026-01-01"))
    return t


if __name__ == "__main__":
    main(build, __file__)

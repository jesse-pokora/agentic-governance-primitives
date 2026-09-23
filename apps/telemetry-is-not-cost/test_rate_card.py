import unittest
from decimal import Decimal

from rate_card import CostRefused, Money, RateCard, Usage, cost, total

USAGE = Usage(model="toy-model", version="2026-01-01",
              input_tokens=10_000, output_tokens=2_000)
CARD = RateCard(model="toy-model", version="2026-01-01", currency="USD",
                per_1k_input=Decimal("0.003"), per_1k_output=Decimal("0.015"),
                effective_from="2026-01-01")


class TelemetryIsNotCostTests(unittest.TestCase):
    def test_usage_and_a_matching_card_produce_an_amount(self):
        amount = cost(USAGE, CARD)

        self.assertEqual(amount.currency, "USD")
        self.assertEqual(amount.amount, Decimal("0.060"))

    def test_a_token_count_alone_cannot_be_converted(self):
        with self.assertRaises(CostRefused) as ctx:
            cost(USAGE, None)

        self.assertEqual(ctx.exception.reason, "no_rate_card")

    def test_usage_carries_no_currency_and_no_cost_method(self):
        # The type itself refuses to imply money.
        self.assertFalse(hasattr(USAGE, "cost"))
        self.assertFalse(hasattr(USAGE, "currency"))

    def test_a_card_for_another_model_is_refused(self):
        other = RateCard("other-model", "2026-01-01", "USD",
                         Decimal("0.001"), Decimal("0.002"), "2026-01-01")

        with self.assertRaises(CostRefused) as ctx:
            cost(USAGE, other)

        self.assertEqual(ctx.exception.reason, "rate_card_mismatch")

    def test_a_card_for_another_version_of_the_same_model_is_refused(self):
        newer = RateCard("toy-model", "2026-06-01", "USD",
                         Decimal("0.004"), Decimal("0.020"), "2026-06-01")

        with self.assertRaises(CostRefused) as ctx:
            cost(USAGE, newer)

        self.assertEqual(ctx.exception.reason, "rate_card_mismatch")

    def test_input_and_output_are_priced_separately(self):
        input_only = Usage("toy-model", "2026-01-01", 10_000, 0)
        output_only = Usage("toy-model", "2026-01-01", 0, 10_000)

        self.assertNotEqual(cost(input_only, CARD).amount,
                            cost(output_only, CARD).amount)

    def test_amounts_in_the_same_currency_add(self):
        combined = total(cost(USAGE, CARD), cost(USAGE, CARD))

        self.assertEqual(combined.amount, Decimal("0.120"))

    def test_amounts_in_different_currencies_will_not_add(self):
        with self.assertRaises(CostRefused) as ctx:
            total(Money(Decimal("1.00"), "USD"), Money(Decimal("1.00"), "EUR"))

        self.assertEqual(ctx.exception.reason, "currency_mismatch")

    def test_a_card_without_a_currency_is_refused(self):
        with self.assertRaises(CostRefused) as ctx:
            RateCard("toy-model", "2026-01-01", "", Decimal("0.003"),
                     Decimal("0.015"), "2026-01-01")

        self.assertEqual(ctx.exception.reason, "currency_missing")

    def test_a_negative_rate_is_refused(self):
        with self.assertRaises(CostRefused) as ctx:
            RateCard("toy-model", "2026-01-01", "USD", Decimal("-0.003"),
                     Decimal("0.015"), "2026-01-01")

        self.assertEqual(ctx.exception.reason, "negative_rate")

    def test_negative_usage_is_refused(self):
        with self.assertRaises(CostRefused) as ctx:
            cost(Usage("toy-model", "2026-01-01", -1, 0), CARD)

        self.assertEqual(ctx.exception.reason, "invalid_usage")

    def test_totalling_nothing_is_refused(self):
        with self.assertRaises(CostRefused) as ctx:
            total()

        self.assertEqual(ctx.exception.reason, "nothing_to_total")


if __name__ == "__main__":
    unittest.main()

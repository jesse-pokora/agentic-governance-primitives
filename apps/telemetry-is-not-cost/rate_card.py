"""Telemetry is not cost.

A token count becomes a monetary figure only against a pinned rate card for
that exact model and version. A cost reported without one is refused, and two
amounts in different currencies will not add.

Token counts get quoted as money constantly, because they are the number that
happens to be in the log. They are a measure of work, not of spend: the rate
changes, differs per model, differs between input and output, and is not
knowable from the count at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


class CostRefused(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Usage:
    """Measured work. Deliberately has no cost method and no currency."""

    model: str
    version: str
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class RateCard:
    model: str
    version: str
    currency: str
    per_1k_input: Decimal
    per_1k_output: Decimal
    effective_from: str

    def __post_init__(self) -> None:
        if self.per_1k_input < 0 or self.per_1k_output < 0:
            raise CostRefused("negative_rate", f"{self.model} {self.version}")
        if not self.currency:
            raise CostRefused("currency_missing", f"{self.model} {self.version}")


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            # Summing across currencies needs an exchange rate, which is
            # another pinned fact nobody supplied.
            raise CostRefused(
                "currency_mismatch", f"{self.currency} + {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)


def cost(usage: Usage, card: RateCard | None) -> Money:
    """Convert measured usage into money, or refuse."""
    if card is None:
        raise CostRefused(
            "no_rate_card",
            "a token count is a measure of work, not an amount of money",
        )
    if (card.model, card.version) != (usage.model, usage.version):
        # A rate card for a different model is a guess wearing a decimal point.
        raise CostRefused(
            "rate_card_mismatch",
            f"card is for {card.model} {card.version}, usage is "
            f"{usage.model} {usage.version}",
        )
    if usage.input_tokens < 0 or usage.output_tokens < 0:
        raise CostRefused("invalid_usage", f"{usage.model} {usage.version}")

    amount = (
        Decimal(usage.input_tokens) / 1000 * card.per_1k_input
        + Decimal(usage.output_tokens) / 1000 * card.per_1k_output
    )
    return Money(amount, card.currency)


def total(*amounts: Money) -> Money:
    if not amounts:
        raise CostRefused("nothing_to_total", "no amounts given")
    running = amounts[0]
    for amount in amounts[1:]:
        running = running + amount
    return running

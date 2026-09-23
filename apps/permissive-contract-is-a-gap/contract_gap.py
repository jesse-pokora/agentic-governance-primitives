"""A permissive contract is a gap.

If a schema admits a value the instruction forbids, that is a gap — recorded
even when no artifact currently sends such a value. The contract is what will
be enforced tomorrow; today's well-behaved artifacts are not evidence about it.

The failure this catches is the most comfortable kind. Every sample passes,
every test is green, and the only thing holding the line is that nobody has
yet sent the empty string the schema has always accepted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable


class ContractRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Rule:
    """An instruction, plus a probe the contract must reject to satisfy it."""

    id: str
    text: str
    forbidden_examples: tuple[Any, ...]

    def __post_init__(self) -> None:
        if not self.forbidden_examples:
            # A rule with nothing it forbids cannot be violated, so a contract
            # cannot fail it, so declaring it proves nothing.
            raise ContractRejected("rule_forbids_nothing", self.id)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    status: str  # "enforced" or "contract_gap"
    admitted: tuple[str, ...] = ()


def string_schema(min_length: int = 0, pattern: str | None = None) -> Callable[[Any], bool]:
    """A toy validator: returns True when the contract *admits* the value."""
    compiled = re.compile(pattern) if pattern else None

    def admits(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        if len(value) < min_length:
            return False
        if compiled and not compiled.fullmatch(value):
            return False
        return True

    return admits


def audit(contract: Callable[[Any], bool], rules: list[Rule]) -> tuple[Finding, ...]:
    """Ask the contract about each rule's forbidden values.

    Note what is *not* consulted: any real artifact. The question is what the
    contract permits, not what has so far been sent through it.
    """
    if not rules:
        raise ContractRejected("no_rules", "a contract audited against nothing passes")

    findings = []
    for rule in rules:
        admitted = tuple(
            repr(value) for value in rule.forbidden_examples if contract(value)
        )
        findings.append(
            Finding(
                rule_id=rule.id,
                status="contract_gap" if admitted else "enforced",
                admitted=admitted,
            )
        )
    return tuple(findings)


def gaps(findings: tuple[Finding, ...]) -> tuple[Finding, ...]:
    return tuple(f for f in findings if f.status == "contract_gap")

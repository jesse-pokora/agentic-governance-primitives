"""Unproven isolation fails closed.

A run proceeds only when isolation is *verified*. An operator assertion that a
sandbox exists is recorded as an assertion and never counted as evidence, and a
child process advertising restricted capabilities proves nothing about the
operating system it runs on.

The distinction this app is built around: a claim about the world and a
measurement of the world are different objects, and a governance system that
stores them in the same field has already lost the argument.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class IsolationUnproven(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Assertion:
    """Somebody said isolation is in place. That is all this is."""

    claimed_by: str
    mechanism: str


@dataclass(frozen=True)
class Probe:
    """A measurement: a named check that actually ran and returned a result."""

    name: str
    passed: bool


@dataclass(frozen=True)
class CapabilityDeclaration:
    """What a child process says about itself."""

    denies_write: bool
    denies_terminal: bool


@dataclass
class IsolationRecord:
    verified: bool
    probes: tuple[Probe, ...] = ()
    assertions: tuple[Assertion, ...] = ()
    declarations: tuple[CapabilityDeclaration, ...] = ()


def evaluate_isolation(
    probes: list[Probe],
    assertions: list[Assertion] | None = None,
    declarations: list[CapabilityDeclaration] | None = None,
    allow_unisolated: bool = False,
    local_development_proof: Callable[[], bool] | None = None,
) -> IsolationRecord:
    """Verify isolation, or refuse.

    Assertions and capability declarations are carried into the record for
    audit and contribute nothing to the verdict. Only probes do.

    `allow_unisolated` is the local-development escape hatch, and it is not
    honoured on its own: it requires a proof callable that actually returns
    True. A bypass flag that works because it was passed is a bypass flag that
    works in production.
    """
    assertions = tuple(assertions or ())
    declarations = tuple(declarations or ())
    probes_t = tuple(probes)

    record = IsolationRecord(
        verified=False, probes=probes_t, assertions=assertions, declarations=declarations
    )

    if allow_unisolated:
        if local_development_proof is None or not local_development_proof():
            raise IsolationUnproven(
                "bypass_not_verifiable",
                "allow_unisolated requires a verifiable local-development context",
            )
        return record  # explicitly unverified, and recorded as such

    if not probes_t:
        raise IsolationUnproven(
            "no_isolation_evidence",
            f"{len(assertions)} assertion(s), {len(declarations)} declaration(s), 0 probes",
        )

    failed = tuple(p.name for p in probes_t if not p.passed)
    if failed:
        raise IsolationUnproven("probe_failed", ", ".join(sorted(failed)))

    record.verified = True
    return record

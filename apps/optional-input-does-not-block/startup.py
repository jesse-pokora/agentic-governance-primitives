"""Optional input does not block.

A run starts when every *required* input is present, even if every optional one
is missing. A missing optional input is recorded and the run is marked
degraded; it is never escalated into a stop.

This app exists as a counterweight. Nearly every other app in this catalog
teaches fail-closed, and a system built only from those refuses to start over
context it never needed. Knowing what *not* to block on is the other half of
the craft, and it is the half that decides whether an agent is usable.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class StartupRefused(Exception):
    def __init__(self, reason: str, missing: tuple[str, ...]):
        super().__init__(f"{reason}: {', '.join(missing)}")
        self.reason = reason
        self.detail = ", ".join(missing)
        self.missing = missing


@dataclass(frozen=True)
class InputSpec:
    name: str
    required: bool


@dataclass
class StartupDecision:
    started: bool
    degraded: bool
    missing_optional: tuple[str, ...] = ()
    extra_context: tuple[str, ...] = ()
    supplied: dict = field(default_factory=dict)


def _is_present(value) -> bool:
    """Present means supplied and non-empty.

    A required field holding "" or None is missing wearing a costume, and
    accepting it is how a required input quietly becomes optional.
    """
    if value is None:
        return False
    if isinstance(value, (str, bytes, list, tuple, dict, set)) and len(value) == 0:
        return False
    return True


def evaluate_startup(specs: list[InputSpec], supplied: dict) -> StartupDecision:
    """Decide whether the run may start.

    Every missing required input is reported at once, not just the first: a
    caller fixing intake should learn the whole list in one round.
    """
    declared = {spec.name for spec in specs}

    missing_required = tuple(
        sorted(s.name for s in specs if s.required and not _is_present(supplied.get(s.name)))
    )
    if missing_required:
        raise StartupRefused("missing_required_input", missing_required)

    missing_optional = tuple(
        sorted(s.name for s in specs if not s.required and not _is_present(supplied.get(s.name)))
    )

    # An input nobody declared is context, not a violation. Intake is the wrong
    # place for a closed schema: the cost of refusing an unexpected field here
    # is a run that cannot start, and the field was never going to be used.
    extra = tuple(sorted(set(supplied) - declared))

    return StartupDecision(
        started=True,
        degraded=bool(missing_optional),
        missing_optional=missing_optional,
        extra_context=extra,
        supplied={k: v for k, v in supplied.items() if _is_present(v)},
    )

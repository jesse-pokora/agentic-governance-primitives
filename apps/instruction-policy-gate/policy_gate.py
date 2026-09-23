"""Instruction policy gate.

Every declared instruction receives an explicit verdict from a fixed
vocabulary. An instruction with no mechanical checker is reported as
`unenforceable` — never counted as satisfied, and never quietly left out of the
report.

That is the whole point. A compliance report that lists only the instructions
somebody wrote a checker for reads as full marks, and the instructions nobody
could check are exactly the ones worth knowing about. The report here always
has one row per declared instruction, so "we comply" and "we checked" stop
being the same sentence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

# A checker returns one of these. `unenforceable` is not among them: it is not
# a checker's verdict, it is what the absence of a checker produces.
CHECKER_VERDICTS = frozenset({"passed", "failed", "not_applicable"})
VERDICTS = CHECKER_VERDICTS | {"unenforceable"}


class PolicyRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Instruction:
    """One instruction, traceable to where it was written down.

    `check` returns (verdict, detail) given the artifact. None means nobody has
    written a mechanical check for this instruction, which is a fact about the
    policy and is reported as such.
    """

    id: str
    text: str
    source: str
    check: Callable[[Any], tuple[str, str]] | None = None

    @property
    def enforceable(self) -> bool:
        return self.check is not None


@dataclass(frozen=True)
class Verdict:
    instruction_id: str
    verdict: str
    detail: str = ""


@dataclass(frozen=True)
class PolicyReport:
    verdicts: tuple[Verdict, ...]

    @property
    def admitted(self) -> bool:
        """Only a `failed` blocks. Unenforceable and not-applicable do not.

        An unenforceable instruction is not evidence of a violation, so it
        cannot fail the artifact — but it is not evidence of compliance
        either, which is what `coverage` is for.
        """
        return not self.failures

    @property
    def failures(self) -> tuple[Verdict, ...]:
        return self.of("failed")

    def of(self, verdict: str) -> tuple[Verdict, ...]:
        if verdict not in VERDICTS:
            raise PolicyRejected("unknown_verdict", verdict)
        return tuple(v for v in self.verdicts if v.verdict == verdict)

    def coverage(self) -> tuple[int, int]:
        """(instructions actually checked, instructions declared).

        The number that stops "nothing failed" from being read as "everything
        was verified".
        """
        checked = sum(1 for v in self.verdicts if v.verdict in CHECKER_VERDICTS)
        return checked, len(self.verdicts)


def evaluate(policy: list[Instruction], artifact: Any) -> PolicyReport:
    """Give every declared instruction a verdict, in declaration order."""
    if not policy:
        raise PolicyRejected("empty_policy", "a policy that declares nothing gates nothing")

    seen: set[str] = set()
    verdicts: list[Verdict] = []

    for instruction in policy:
        if not instruction.id:
            raise PolicyRejected("unidentified_instruction", instruction.text[:60])
        if instruction.id in seen:
            # Two rows with one id make the report unreadable: a reader cannot
            # tell which one a verdict belongs to.
            raise PolicyRejected("duplicate_instruction_id", instruction.id)
        seen.add(instruction.id)

        if instruction.check is None:
            verdicts.append(
                Verdict(instruction.id, "unenforceable", "no mechanical check declared")
            )
            continue

        try:
            verdict, detail = instruction.check(artifact)
        except Exception as error:  # a broken checker, not a failing artifact
            raise PolicyRejected(
                "checker_errored", f"{instruction.id}: {type(error).__name__}"
            ) from None

        if verdict not in CHECKER_VERDICTS:
            # A checker that invents a verdict makes the vocabulary meaningless,
            # and "unenforceable" in particular must never be self-assigned.
            raise PolicyRejected(
                "invalid_verdict", f"{instruction.id} returned {verdict!r}"
            )

        verdicts.append(Verdict(instruction.id, verdict, detail))

    return PolicyReport(verdicts=tuple(verdicts))

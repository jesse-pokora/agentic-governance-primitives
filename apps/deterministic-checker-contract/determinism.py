"""Deterministic checker contract.

A checker must return the same verdict for the same artifact on repeated
evaluation. One that does not is refused, and the refusal names both verdicts.

A checker that is merely usually right is worse than no checker. Its failures
arrive at random, so a red result is re-run until it goes green and nobody
learns anything — and the instruction it guards ends up enforced on whichever
attempts happened to agree with it.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable

MINIMUM_RUNS = 2


class NondeterministicChecker(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def evaluate_repeatedly(
    check: Callable[[Any], Any], artifact: Any, runs: int = 3
) -> Any:
    """Return the verdict, or refuse if the checker cannot agree with itself.

    `runs` is the number of evaluations, and one is not enough: a single run
    cannot disagree with anything, so it can never detect the condition this
    function exists to detect.
    """
    if runs < MINIMUM_RUNS:
        raise NondeterministicChecker(
            "insufficient_runs", f"{runs} < {MINIMUM_RUNS}; one run proves nothing"
        )

    verdicts = []
    for attempt in range(runs):
        try:
            verdicts.append(check(artifact))
        except Exception as error:
            raise NondeterministicChecker(
                "checker_errored", f"run {attempt + 1} raised {type(error).__name__}"
            ) from None

    distinct = Counter(str(v) for v in verdicts)
    if len(distinct) > 1:
        # Report the whole distribution. "Sometimes fails" is not actionable;
        # "3 passed, 2 failed out of 5" is.
        spread = ", ".join(f"{v}x{n}" for v, n in sorted(distinct.items()))
        raise NondeterministicChecker(
            "verdicts_disagree", f"over {runs} runs: {spread}"
        )

    return verdicts[0]


def certify(
    check: Callable[[Any], Any], artifacts: list[Any], runs: int = 3
) -> tuple[Any, ...]:
    """Evaluate a checker over several artifacts, refusing on the first that
    cannot be reproduced.

    Different verdicts for *different* artifacts are the point of a checker.
    Only disagreement about the same artifact is a defect.
    """
    if not artifacts:
        raise NondeterministicChecker("no_artifacts", "nothing to evaluate")
    return tuple(evaluate_repeatedly(check, artifact, runs) for artifact in artifacts)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from determinism import certify, evaluate_repeatedly  # noqa: E402

CLEAN = "result = int(user_input)"
DIRTY = "result = eval(user_input)"


def pure(source):
    return "passed" if "eval(" not in source else "failed"


class Counting:
    def __init__(self):
        self.calls = 0

    def __call__(self, source):
        self.calls += 1
        return "passed" if self.calls % 2 else "failed"


class Clock:
    def __init__(self):
        self.now = 0


class ClockDependent:
    def __init__(self, clock):
        self.clock = clock

    def __call__(self, source):
        self.clock.now += 1
        return "passed" if self.clock.now < 2 else "failed"


def build() -> Trace:
    t = Trace(
        app="deterministic-checker-contract",
        claim=(
            "A checker must return the same verdict for the same artifact on repeated "
            "evaluation — one that does not is refused, and the refusal reports the "
            "whole distribution."
        ),
        enforcement="deterministic",
        denial_type="NondeterministicChecker",
    )
    t.allow("a pure checker, evaluated three times",
            {"artifact": CLEAN, "runs": 3},
            lambda: evaluate_repeatedly(pure, CLEAN),
            evidence=lambda: "every run agreed")
    t.deny("a checker that counts its own calls",
           {"artifact": CLEAN, "runs": 5, "checker": "alternates each call"},
           lambda: evaluate_repeatedly(Counting(), CLEAN, runs=5),
           evidence=lambda: "the distribution is reported, not just the disagreement",
           note="'Sometimes fails' is not actionable. A red result gets re-run until "
                "it goes green and nobody learns anything.")
    t.deny("a checker that consults a clock",
           {"artifact": CLEAN, "runs": 3, "checker": "verdict depends on elapsed ticks"},
           lambda: evaluate_repeatedly(ClockDependent(Clock()), CLEAN))
    t.deny("evaluating only once",
           {"artifact": CLEAN, "runs": 1},
           lambda: evaluate_repeatedly(pure, CLEAN, runs=1),
           note="A single run cannot disagree with anything, so it can never detect "
                "the thing this check exists to detect.")
    t.allow("different verdicts for different artifacts",
            {"artifacts": f"{CLEAN} | {DIRTY}", "runs": 3},
            lambda: list(certify(pure, [CLEAN, DIRTY])),
            evidence=lambda: "only disagreement about the same artifact is a defect")
    t.deny("a checker that raises",
           {"artifact": CLEAN, "checker": "raises RuntimeError"},
           lambda: evaluate_repeatedly(
               lambda s: (_ for _ in ()).throw(RuntimeError("bug")), CLEAN))
    return t


if __name__ == "__main__":
    main(build, __file__)

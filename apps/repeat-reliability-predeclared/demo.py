"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from repeats import Plan, Series  # noqa: E402


def series(*outcomes, runs=5):
    s = Series(plan=Plan(runs=runs, configuration="frozen-toy-config"))
    for outcome in outcomes:
        s.record(outcome)
    return s


def build() -> Trace:
    t = Trace(
        app="repeat-reliability-predeclared",
        claim=(
            "The number of attempts is declared before the first one runs, every "
            "attempt is retained, and a conclusion drawn from fewer than the declared "
            "number is refused."
        ),
        enforcement="deterministic",
        denial_type="SeriesRefused",
    )
    stable = series(*["passed"] * 5)
    t.allow("five declared, five run, all agreeing",
            {"declared": 5, "attempts": "passed x5"},
            lambda: f"stable={stable.conclude().stable}, "
                    f"outcome={stable.conclude().outcome}")
    t.deny("four greens and a temptation to stop",
           {"declared": 5, "attempts": "passed x4"},
           lambda: series(*["passed"] * 4).conclude(),
           note="Run it again because that one looked odd; stop when it is green. "
                "Every step is reasonable, and the series measures the stopping rule "
                "rather than the system.")
    unstable = series("passed", "passed", "failed", "passed", "passed")
    t.allow("five run, one disagreed",
            {"declared": 5, "attempts": "passed, passed, failed, passed, passed"},
            lambda: f"stable={unstable.conclude().stable}, "
                    f"outcome={unstable.conclude().outcome}, "
                    f"distribution={dict(unstable.conclude().distribution)}",
            evidence=lambda: "an unstable series has no outcome",
            note="Reporting the majority would turn 'fails one time in five' into "
                 "'passes', which is the whole failure this app prevents.")
    extra = series(*["passed"] * 5, "failed")
    t.allow("a sixth attempt after the declared five",
            {"declared": 5, "attempts": "passed x5, failed"},
            lambda: f"attempts={extra.conclude().attempts}, "
                    f"stable={extra.conclude().stable}",
            note="Included, not trimmed. Discarding it would be the same selective "
                 "stopping running backwards.")
    all_failed = series(*["failed"] * 5)
    t.allow("five failures",
            {"declared": 5, "attempts": "failed x5"},
            lambda: f"stable={all_failed.conclude().stable}, "
                    f"outcome={all_failed.conclude().outcome}",
            evidence=lambda: "stable means the system agrees with itself, not that the "
                             "news is good")
    t.deny("declaring a single run",
           {"declared": 1},
           lambda: Plan(runs=1, configuration="frozen-toy-config"),
           note="One attempt cannot disagree with anything.")
    return t


if __name__ == "__main__":
    main(build, __file__)

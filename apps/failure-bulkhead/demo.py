"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from bulkhead import FailureBulkhead  # noqa: E402
from demo_trace import Trace, main  # noqa: E402


class FakeClock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now

    def advance(self, ticks):
        self.now += ticks


class Dependency:
    def __init__(self, healthy=False):
        self.calls = 0
        self.healthy = healthy

    def __call__(self):
        self.calls += 1
        if not self.healthy:
            raise RuntimeError("toy dependency is down")
        return "toy result"


def build() -> Trace:
    clock = FakeClock()
    breaker = FailureBulkhead(threshold=3, cooldown=60, clock=clock)
    dependency = Dependency()

    t = Trace(
        app="failure-bulkhead",
        claim=(
            "After a declared number of consecutive failures the breaker opens and every "
            "subsequent call fails fast without invoking the dependency — and it closes "
            "only when an explicit probe, allowed no earlier than a declared cooldown, "
            "actually succeeds."
        ),
        enforcement="deterministic",
        denial_type="BreakerOpen",
    )

    def attempt():
        try:
            return breaker.call(dependency)
        except RuntimeError as err:
            return f"dependency raised: {err}"

    for n in (1, 2):
        t.allow(
            f"failure {n}, below the threshold of 3",
            {"state": breaker.state, "consecutive failures": breaker.consecutive_failures},
            attempt,
            evidence=lambda: f"dependency invoked {dependency.calls} time(s); state "
                             f"{breaker.state}",
        )
    t.allow(
        "failure 3 reaches the threshold and opens the breaker",
        {"state": "closed", "consecutive failures": 2, "threshold": 3},
        attempt,
        evidence=lambda: f"state {breaker.state}; opened at tick {breaker.opened_at}",
    )
    before = dependency.calls
    t.deny(
        "the next fifty calls, with the breaker open",
        {"state": "open", "calls attempted": 50},
        lambda: [breaker.call(dependency) for _ in range(50)],
        evidence=lambda: f"dependency invoked {dependency.calls - before} more times",
        note="The retries are what carry one broken service outward into a queue of "
             "stuck runs. This is the thousandth error, not the first.",
    )
    clock.advance(10_000)
    t.deny(
        "a normal call long after the cooldown elapsed",
        {"state": "open", "ticks since opening": 10_000, "cooldown": 60},
        lambda: breaker.call(dependency),
        note="Time passing is not evidence of recovery. A breaker that closed on a "
             "timer would decide a service is healthy without ever asking it.",
    )
    dependency.healthy = False
    t.deny(
        "a probe that finds the dependency still down",
        {"state": "open", "cooldown": "elapsed"},
        lambda: breaker.probe(dependency),
        evidence=lambda: f"reopened at tick {breaker.opened_at}; cooldown restarted",
    )
    t.deny(
        "a second probe immediately afterwards",
        {"ticks since reopening": 0, "cooldown": 60},
        lambda: breaker.probe(dependency),
        note="A failed probe restarts the cooldown, or a down dependency gets hammered "
             "on every call once the first cooldown passes.",
    )
    clock.advance(60)
    dependency.healthy = True
    t.allow(
        "a probe that finds the dependency healthy",
        {"ticks since reopening": 60, "cooldown": 60},
        lambda: breaker.probe(dependency),
        evidence=lambda: f"state {breaker.state}; transitions "
                         f"{[(x.to, x.reason) for x in breaker.history]}",
    )
    return t


if __name__ == "__main__":
    main(build, __file__)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from grounding import Claim, GroundTruth, verify_claims  # noqa: E402

TRUTH = GroundTruth({
    "svc-fake-a.owner": "toy-team-alpha",
    "svc-fake-a.replicas": "4",
    "svc-fake-b.owner": "toy-team-beta",
})
HELD = "svc-fake-a.owner=toy-team-alpha, svc-fake-a.replicas=4, svc-fake-b.owner=toy-team-beta"


def build() -> Trace:
    t = Trace(
        app="grounded-claim-verification",
        claim=(
            "Every factual claim a model emits must name a ground-truth key that exists "
            "and quote that record's value exactly — an uncited claim, an invented "
            "source, or an altered quote fails closed."
        ),
        enforcement="deterministic",
        denial_type="GroundingRejected",
    )
    t.allow("claims that cite held records and quote them exactly",
            {"claim": "svc-fake-a runs 4 replicas",
             "cites": "svc-fake-a.replicas", "quotes": "4", "held": HELD},
            lambda: verify_claims(
                [Claim("svc-fake-a is owned by toy-team-alpha", "svc-fake-a.owner", "toy-team-alpha"),
                 Claim("svc-fake-a runs 4 replicas", "svc-fake-a.replicas", "4")], TRUTH)
                or "2 claims grounded")
    t.deny("a claim with no citation at all",
           {"claim": "svc-fake-a is probably fine", "cites": "nothing"},
           lambda: verify_claims([Claim("svc-fake-a is probably fine", None, None)], TRUTH))
    t.deny("a citation to a key that does not exist",
           {"claim": "svc-fake-c is owned by toy-team-gamma",
            "cites": "svc-fake-c.owner", "held": HELD},
           lambda: verify_claims(
               [Claim("svc-fake-c is owned by toy-team-gamma", "svc-fake-c.owner",
                      "toy-team-gamma")], TRUTH),
           note="The most convincing drift, because it looks cited. A check that only "
                "asks 'is there a citation?' passes it.")
    t.deny("the right key, quoting a value that drifted",
           {"claim": "svc-fake-a runs 8 replicas", "cites": "svc-fake-a.replicas",
            "quotes": "8", "record holds": "4"},
           lambda: verify_claims(
               [Claim("svc-fake-a runs 8 replicas", "svc-fake-a.replicas", "8")], TRUTH),
           note="The characteristic shape of a cheaper or degraded model: the structure "
                "survives, the content slips.")
    t.deny("a near-miss quote differing only in case",
           {"cites": "svc-fake-a.owner", "quotes": "toy-team-Alpha",
            "record holds": "toy-team-alpha"},
           lambda: verify_claims(
               [Claim("owner", "svc-fake-a.owner", "toy-team-Alpha")], TRUTH),
           note="Comparison is exact. An exact gate can be loosened deliberately; a "
                "fuzzy one can never be tightened back with confidence.")
    return t


if __name__ == "__main__":
    main(build, __file__)

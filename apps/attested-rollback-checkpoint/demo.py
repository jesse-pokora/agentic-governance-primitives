"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from rollback import AttestedCheckpointStore, digest_of  # noqa: E402

V1 = {"config": {"replicas": 1}, "release": "toy-v1"}
V2 = {"config": {"replicas": 4}, "release": "toy-v2"}
V3 = {"config": {"replicas": 9}, "release": "toy-v3"}


def build() -> Trace:
    store = AttestedCheckpointStore()
    v1, v2 = store.attest(V1), store.attest(V2)
    t = Trace(
        app="attested-rollback-checkpoint",
        claim=(
            "A rollback restores exactly a previously attested state digest, failing "
            "closed on an unattested target or a checkpoint whose bytes no longer hash "
            "to it."
        ),
        enforcement="deterministic",
        denial_type="RollbackDenied",
    )
    t.allow("rolling back to a state that was attested here",
            {"target": v1[:20] + "...", "attested": "toy-v1, toy-v2"},
            lambda: store.rollback(v1),
            evidence=lambda: f"restored digest re-hashes to the target: "
                             f"{digest_of(store.rollback(v1)) == v1}")
    t.deny("a correct digest for a state that was never attested here",
           {"target": digest_of(V3)[:20] + "...", "state": "toy-v3 exists elsewhere",
            "attested": "toy-v1, toy-v2"},
           lambda: store.rollback(digest_of(V3)),
           note="'Restore whatever the caller names' is an unaudited write with a "
                "friendly name.")
    store._by_digest[v1] = '{"release":"toy-substituted"}'
    t.deny("the index still says toy-v1, but the stored bytes were substituted",
           {"target": v1[:20] + "...", "filed under": "toy-v1",
            "bytes now hash to": "something else"},
           lambda: store.rollback(v1),
           evidence=lambda: "the store does not trust its own index",
           note="Trusting the index alone hands back the wrong state under a trusted "
                "name, which is worse than failing.")
    t.deny("rolling back before anything has been attested",
           {"store": "empty", "target": digest_of(V1)[:20] + "..."},
           lambda: AttestedCheckpointStore().rollback(digest_of(V1)))
    return t


if __name__ == "__main__":
    main(build, __file__)

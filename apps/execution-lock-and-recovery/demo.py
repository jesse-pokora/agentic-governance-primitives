"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from lock_manager import ExecutionLockManager  # noqa: E402


def build() -> Trace:
    manager = ExecutionLockManager()
    challenge = manager.acquire("run-toy-1")
    t = Trace(
        app="execution-lock-and-recovery",
        claim=(
            "A crashed run leaves a lock that only an explicit, challenge-authenticated "
            "operator attestation can clear — the system never infers liveness on its own."
        ),
        enforcement="deterministic",
        denial_type="LockHeld / RecoveryDenied",
        redactions={challenge: "<challenge issued at acquire>"},
    )
    t.deny("a second run tries to take a lock that is already held",
           {"run_id": "run-toy-1", "state": "held since the first acquire"},
           lambda: manager.acquire("run-toy-1"),
           evidence=lambda: f"locked: {manager.is_locked('run-toy-1')}",
           note="The first holder may have crashed. The lock manager has no way to "
                "know that, and does not guess.")
    t.deny("clearing the lock with the wrong challenge",
           {"run_id": "run-toy-1", "attested": "0000...0000"},
           lambda: manager.clear("run-toy-1", "0" * 64),
           evidence=lambda: f"locked: {manager.is_locked('run-toy-1')}",
           note="No timeout, no heartbeat, no 'probably dead by now'. Inferring "
                "liveness is how two runs end up writing at once.")
    t.allow("an operator attests the exact challenge",
            {"run_id": "run-toy-1", "attested": challenge},
            lambda: manager.clear("run-toy-1", challenge) or "lock cleared",
            evidence=lambda: f"locked: {manager.is_locked('run-toy-1')}")
    t.allow("the next run can now acquire it",
            {"run_id": "run-toy-1"},
            lambda: "<a fresh challenge>",
            evidence=lambda: "a fresh challenge is issued for this holder")
    return t


if __name__ == "__main__":
    main(build, __file__)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from memory_store import MemoryRecord, QuarantiningMemoryStore  # noqa: E402

ALPHA = MemoryRecord("svc-fake-a.owner", "toy-team-alpha", "run-1")
ALPHA_AGAIN = MemoryRecord("svc-fake-a.owner", "toy-team-alpha", "run-2")
BETA = MemoryRecord("svc-fake-a.owner", "toy-team-beta", "run-3")


def build() -> Trace:
    store = QuarantiningMemoryStore()
    t = Trace(
        app="memory-conflict-quarantine",
        claim=(
            "When two memory records assert different values for the same key, both are "
            "retained and the conflict is surfaced — the newer one never silently "
            "overwrites the older, and the key has no answer until someone resolves it."
        ),
        enforcement="deterministic",
        denial_type="MemoryRejected",
    )
    t.verdict("run-1 writes a key nobody has claimed",
              {"key": "svc-fake-a.owner", "value": "toy-team-alpha", "source": "run-1"},
              lambda: store.write(ALPHA), lambda settled: settled,
              lambda settled: "settled",
              evidence=lambda: f"quarantine holds {len(store.quarantine)} conflicts")
    t.verdict("run-2 asserts the same value from a different source",
              {"key": "svc-fake-a.owner", "value": "toy-team-alpha", "source": "run-2"},
              lambda: store.write(ALPHA_AGAIN), lambda settled: settled,
              lambda settled: "settled — corroboration, not conflict")
    t.verdict("run-3 asserts a different value for the same key",
              {"key": "svc-fake-a.owner", "value": "toy-team-beta", "source": "run-3",
               "held": "toy-team-alpha (run-1)"},
              lambda: store.write(BETA), lambda settled: settled,
              lambda settled: "quarantined — both records retained",
              evidence=lambda: f"quarantine holds {len(store.quarantine)} conflict; "
                               f"both sources still attributable",
              note="Under last-write-wins the drift becomes the memory and the record "
                   "it replaced is gone. A model that drifts writes its drift last.")
    t.deny("reading a key that is under conflict",
           {"key": "svc-fake-a.owner", "candidates": "toy-team-alpha, toy-team-beta"},
           lambda: store.read("svc-fake-a.owner"),
           note="Returning either side would be the silent choice the store exists to "
                "prevent. Returning the older one is last-write-wins with extra steps.")
    t.deny("resolving the conflict to a value nobody asserted",
           {"key": "svc-fake-a.owner", "chosen": "toy-team-gamma",
            "asserted": "toy-team-alpha, toy-team-beta"},
           lambda: store.resolve("svc-fake-a.owner",
                                 MemoryRecord("svc-fake-a.owner", "toy-team-gamma", "human")),
           note="Resolution is a decision between what was asserted.")
    return t


if __name__ == "__main__":
    main(build, __file__)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from concurrent_ledger import ConcurrentLedger  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

WRITERS = 8


def race(ledger, method):
    """Every thread reads the head before the barrier releases them, so all
    eight genuinely build on the same predecessor."""
    barrier = threading.Barrier(WRITERS)
    accepted, rejected, guard = [], [], threading.Lock()

    def writer(n):
        head = ledger.head_hash()
        barrier.wait()
        try:
            index = (ledger.append_cas({"actor": f"agent-{n}"}, head)
                     if method == "cas" else ledger.append_locked({"actor": f"agent-{n}"}))
        except Exception:
            with guard:
                rejected.append(n)
        else:
            with guard:
                accepted.append(index)

    threads = [threading.Thread(target=writer, args=(n,)) for n in range(WRITERS)]
    for t_ in threads:
        t_.start()
    for t_ in threads:
        t_.join()
    return accepted, rejected


def build() -> Trace:
    t = Trace(
        app="concurrent-append-integrity",
        claim=(
            "Under concurrent writers an append-only ledger admits exactly one entry per "
            "accepted append, with contiguous indices and an unbroken hash chain — a "
            "writer whose predecessor moved is rejected."
        ),
        enforcement="deterministic",
        denial_type="ConcurrentAppendRejected",
    )
    unsafe = ConcurrentLedger()
    head = unsafe.head_hash()
    unsafe.append_unsafe({"actor": "agent-a"}, head)
    unsafe.append_unsafe({"actor": "agent-b"}, head)
    t.verdict("two uncoordinated writers that both read the same head",
              {"writer a": "prev_hash = genesis", "writer b": "prev_hash = genesis (stale)",
               "coordination": "none"},
              unsafe.verify, lambda r: r.valid,
              lambda r: "chain intact" if r.valid else f"{r.reason} at entry {r.first_bad_index}",
              evidence=lambda: "the hazard, staged as an explicit interleaving rather "
                               "than a race, so it is deterministic",
              note="Both entries claim the same predecessor. The chain no longer "
                   "describes an order.")

    cas = ConcurrentLedger()
    accepted, rejected = race(cas, "cas")
    t.verdict(f"{WRITERS} threads racing, each naming the head it built on",
              {"writers": WRITERS, "discipline": "compare-and-swap",
               "all read head": "before the barrier released"},
              cas.verify, lambda r: r.valid,
              lambda r: "chain intact" if r.valid else r.reason,
              evidence=lambda: f"{len(accepted)} accepted, {len(rejected)} rejected as "
                               f"head_moved; ledger holds {len(cas.entries)} entry",
              note="Exactly one wins. The assertion holds under every possible "
                   "scheduling, so the test is not timing-dependent.")

    locked = ConcurrentLedger()
    acc2, rej2 = race(locked, "locked")
    t.verdict(f"{WRITERS} threads serialized through one lock",
              {"writers": WRITERS, "discipline": "read head and extend under a lock"},
              locked.verify, lambda r: r.valid,
              lambda r: "chain intact" if r.valid else r.reason,
              evidence=lambda: f"{len(acc2)} accepted, {len(rej2)} rejected; indices "
                               f"{[e.index for e in locked.entries]}",
              note="No gaps, no duplicates, nothing lost — the other legitimate "
                   "discipline.")
    return t


if __name__ == "__main__":
    main(build, __file__)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from reconciliation import reconcile  # noqa: E402


def build() -> Trace:
    def boom():
        raise RuntimeError("toy upstream failure")

    batch = {
        "asset-a": lambda: "stored",
        "asset-b": boom,
        "asset-c": lambda: "stored",
        "asset-d": boom,
    }
    outcomes = reconcile(dict(batch))

    t = Trace(
        app="canonical-outcome-reconciliation",
        claim=(
            "Every input key in a batch receives exactly one attributable success or "
            "failure outcome, in a fixed order — nothing silently dropped, nothing "
            "double-counted."
        ),
        enforcement="deterministic",
        denial_type="n/a — this app returns one Outcome per key",
    )
    t.verdict("a batch where half the actions fail",
              {"keys": ", ".join(batch), "failing": "asset-b, asset-d"},
              lambda: reconcile(dict(batch)),
              lambda outs: len(outs) == len(batch),
              lambda outs: f"{len(outs)} outcomes for {len(batch)} keys",
              evidence=lambda: ", ".join(f"{o.key}={o.status}" for o in outcomes),
              note="A failure partway through does not truncate the batch. Every key "
                   "is still attempted and still answered.")
    t.verdict("no key is dropped and no key is answered twice",
              {"input keys": len(batch), "check": "set of outcome keys == set of input keys"},
              lambda: [o.key for o in reconcile(dict(batch))],
              lambda keys: sorted(keys) == sorted(batch) and len(keys) == len(set(keys)),
              lambda keys: f"{len(set(keys))} distinct keys, {len(keys)} outcomes",
              note="Dropped and double-counted both leave a total that still looks "
                   "plausible.")
    t.verdict("outcomes arrive in the batch's own order, run after run",
              {"call 1": "reconcile(batch)", "call 2": "reconcile(batch)"},
              lambda: ([o.key for o in reconcile(dict(batch))],
                       [o.key for o in reconcile(dict(batch))]),
              lambda pair: pair[0] == pair[1] == list(batch),
              lambda pair: " -> ".join(pair[0]),
              evidence=lambda: "fixed order, so two runs can be compared line by line")
    return t


if __name__ == "__main__":
    main(build, __file__)

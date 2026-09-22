"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from primitives import canonical_json, content_hash, is_safe_id  # noqa: E402


def build() -> Trace:
    a = {"b": 2, "a": 1, "nested": {"z": 26, "y": 25}}
    b = {"nested": {"y": 25, "z": 26}, "a": 1, "b": 2}

    t = Trace(
        app="deterministic-primitives-kit",
        claim=(
            "The same input byte-for-byte always produces the same canonical JSON, the "
            "same hash, and the same safe-ID validation — across restarts, across "
            "machines."
        ),
        enforcement="deterministic",
        denial_type="n/a — these are pure functions returning values",
    )
    t.verdict("two dicts built in different key orders",
              {"dict A": '{"b":2,"a":1,"nested":{"z":26,"y":25}}',
               "dict B": '{"nested":{"y":25,"z":26},"a":1,"b":2}'},
              lambda: (canonical_json(a), canonical_json(b)),
              lambda pair: pair[0] == pair[1],
              lambda pair: pair[0],
              evidence=lambda: f"same hash: {content_hash(a)[:24]}...",
              note="Insertion order is an accident of how a value was built. A "
                   "canonical form is what makes two values comparable at all.")
    t.verdict("hashing the same value twice in the same process",
              {"value": "dict A", "calls": 2},
              lambda: (content_hash(a), content_hash(a)),
              lambda pair: pair[0] == pair[1],
              lambda pair: pair[0][:32] + "...",
              evidence=lambda: "no clock, no randomness, no locale, no environment")
    for label, value, ok in (
        ("a well-formed id", "toy-run-01", True),
        ("an id with an uppercase letter", "Toy-Run-01", False),
        ("an id starting with a hyphen", "-toy-run", False),
        ("an id of 80 characters", "t" * 80, False),
    ):
        t.verdict(label, {"value": value if len(value) < 40 else value[:20] + f"... ({len(value)} chars)"},
                  lambda v=value: is_safe_id(v), lambda r: r,
                  lambda r: "accepted" if r else "rejected")
    return t


if __name__ == "__main__":
    main(build, __file__)

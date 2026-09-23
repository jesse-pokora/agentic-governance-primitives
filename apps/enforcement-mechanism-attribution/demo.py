"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from mechanism import MECHANISMS, compare, record  # noqa: E402


def build() -> Trace:
    t = Trace(
        app="enforcement-mechanism-attribution",
        claim=(
            "A result that does not name the mechanism enforcing an instruction cannot "
            "be compared with one that does."
        ),
        enforcement="deterministic",
        denial_type="Incomparable",
    )
    t.allow("the same instruction as prose, then behind a gate",
            {"r1": "prose, not followed", "r2": "gate, followed",
             "scale": " < ".join(MECHANISMS)},
            lambda: compare(record("r1", "INS-001", "prose", False),
                            record("r2", "INS-001", "gate", True)).verdict,
            evidence=lambda: "the instruction needs enforcement, not better wording")
    t.allow("an instruction followed under prose alone",
            {"r1": "prose, followed", "r2": "gate, followed"},
            lambda: compare(record("r1", "INS-002", "prose", True),
                            record("r2", "INS-002", "gate", True)).verdict,
            note="A gate here would be cost without benefit. This is the comparison "
                 "that stops a policy accumulating machinery it does not need.")
    t.allow("an instruction ignored under both",
            {"r1": "prose, not followed", "r2": "hook, not followed"},
            lambda: compare(record("r1", "INS-003", "prose", False),
                            record("r2", "INS-003", "hook", False)).verdict,
            evidence=lambda: "neither the wording nor that enforcement is the problem")
    t.deny("one of the results never recorded its mechanism",
           {"r1": "mechanism not recorded", "r2": "gate, followed"},
           lambda: compare(record("r1", "INS-001", None, False),
                           record("r2", "INS-001", "gate", True)),
           note="Not a data point about the instruction — a data point about an "
                "unknown.")
    t.deny("both results used the same mechanism",
           {"r1": "gate, followed", "r2": "gate, not followed"},
           lambda: compare(record("r1", "INS-001", "gate", True),
                           record("r2", "INS-001", "gate", False)),
           note="That compares runs, not mechanisms.")
    t.deny("the results are about different instructions",
           {"r1": "INS-001 under prose", "r2": "INS-002 under gate"},
           lambda: compare(record("r1", "INS-001", "prose", True),
                           record("r2", "INS-002", "gate", True)))
    t.deny("a mechanism outside the vocabulary",
           {"mechanism": "vibes", "vocabulary": ", ".join(MECHANISMS)},
           lambda: record("r1", "INS-001", "vibes", True))
    return t


if __name__ == "__main__":
    main(build, __file__)

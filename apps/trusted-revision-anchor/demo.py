"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from revision_ledger import RevisionLedger  # noqa: E402


def build() -> Trace:
    ledger = RevisionLedger()
    t = Trace(
        app="trusted-revision-anchor",
        claim=(
            "The \"current\" commit is selected only from a ledger slot position, never "
            "from caller-supplied input; \"fresh\" means \"at the ledger head,\" not "
            "\"recent by clock time.\""
        ),
        enforcement="deterministic",
        denial_type="NoRevisionsRecorded",
    )
    t.deny("asking for the current commit before anything was recorded",
           {"ledger": "empty", "call": "current()"},
           ledger.current,
           note="No default, no 'HEAD', no guess.")
    for commit in ("aaa1111", "bbb2222", "ccc3333"):
        ledger.record(commit)
    t.allow("the current commit comes from the ledger head",
            {"recorded": "aaa1111, bbb2222, ccc3333", "call": "current()"},
            ledger.current,
            evidence=lambda: "current() takes no argument at all, so a caller cannot "
                             "suggest an answer")
    t.allow("the head commit is fresh",
            {"commit": "ccc3333", "slot position": ledger.slot_position("ccc3333")},
            lambda: ledger.is_fresh("ccc3333"),
            evidence=lambda: "freshness is position in the ledger, not wall-clock age")
    t.verdict("an earlier commit is not fresh, however recently it arrived",
              {"commit": "aaa1111", "slot position": ledger.slot_position("aaa1111"),
               "head position": ledger.slot_position("ccc3333")},
              lambda: ledger.is_fresh("aaa1111"), lambda v: v,
              lambda v: "fresh" if v else "not fresh — behind the head",
              note="'Recent by clock' and 'at the head' are different questions, and "
                   "only one of them is safe to act on.")
    t.verdict("a commit the ledger never recorded is never fresh",
              {"commit": "zzz9999", "slot position": "none"},
              lambda: ledger.is_fresh("zzz9999"), lambda v: v,
              lambda v: "fresh" if v else "not fresh — unknown to the ledger")
    return t


if __name__ == "__main__":
    main(build, __file__)

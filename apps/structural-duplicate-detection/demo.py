"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from fingerprint import duplicates, fingerprints  # noqa: E402

EXISTING = ("def normalize_path(raw):\n"
            "    cleaned = raw.strip()\n"
            "    if not cleaned:\n"
            "        return None\n"
            "    return cleaned.lower()\n")

REIMPLEMENTED = ("def tidy_path_value(value):\n"
                 "    trimmed = value.strip()\n"
                 "    if not trimmed:\n"
                 "        return None\n"
                 "    return trimmed.lower()\n")

DIFFERENT = "def normalize_path(raw):\n    return raw.replace(chr(92), '/')\n"


def one(source):
    return fingerprints(source)[0].fingerprint


def build() -> Trace:
    t = Trace(
        app="structural-duplicate-detection",
        claim=(
            "Two functions with the same implementation shape produce the same "
            "fingerprint regardless of their names, so a re-implementation under a new "
            "name is detected exactly."
        ),
        enforcement="deterministic",
        denial_type="n/a — this app returns fingerprints and groups",
    )
    t.verdict("the existing helper, and what an agent wrote having forgotten it",
              {"existing": EXISTING.replace("\n", " / ").strip(),
               "written": REIMPLEMENTED.replace("\n", " / ").strip()},
              lambda: (one(EXISTING), one(REIMPLEMENTED)),
              lambda pair: pair[0] == pair[1],
              lambda pair: f"same fingerprint: {pair[0][:24]}...",
              evidence=lambda: "names are the one part guaranteed to differ, so the "
                               "fingerprint discards them",
              note="Nothing notices this normally, because nothing is looking for the "
                   "shape.")
    t.verdict("a genuinely different implementation of the same idea",
              {"existing": "strip, lower", "other": "replace backslashes"},
              lambda: (one(EXISTING), one(DIFFERENT)),
              lambda pair: pair[0] != pair[1],
              lambda pair: "different fingerprints",
              note="Not reported, and that is the boundary: catching it needs "
                   "similarity scoring, which needs a threshold somebody picks.")
    t.verdict("the same body with renamed parameters",
              {"a": "def f(alpha, beta): return alpha + beta",
               "b": "def g(x, y): return x + y"},
              lambda: (one("def f(alpha, beta):\n    return alpha + beta\n"),
                       one("def g(x, y):\n    return x + y\n")),
              lambda pair: pair[0] == pair[1],
              lambda pair: "same fingerprint")
    t.verdict("the same body with a docstring added",
              {"a": "def f(x): return x + 1",
               "b": 'def f(x): """Explains."""; return x + 1'},
              lambda: (one("def f(x):\n    return x + 1\n"),
                       one('def f(x):\n    """Explains the thing."""\n    return x + 1\n')),
              lambda pair: pair[0] == pair[1],
              lambda pair: "same fingerprint")
    t.verdict("one changed constant",
              {"a": "def f(x): return x + 1", "b": "def f(x): return x + 2"},
              lambda: (one("def f(x):\n    return x + 1\n"),
                       one("def f(x):\n    return x + 2\n")),
              lambda pair: pair[0] != pair[1],
              lambda pair: "different fingerprints",
              note="Two functions differing only in a constant are doing different "
                   "things. Collapsing them would make the fingerprint lie.")
    t.verdict("one different helper call",
              {"a": "def f(x): return clean(x)", "b": "def f(x): return scrub(x)"},
              lambda: (one("def f(x):\n    return clean(x)\n"),
                       one("def f(x):\n    return scrub(x)\n")),
              lambda pair: pair[0] != pair[1],
              lambda pair: "different fingerprints",
              evidence=lambda: "only names bound inside the function are normalized away")
    groups = duplicates(EXISTING, REIMPLEMENTED)
    t.allow("scanning two modules for duplicate shapes",
            {"module a": "normalize_path", "module b": "tidy_path_value"},
            lambda: [sorted(item.name for item in group) for group in groups],
            evidence=lambda: f"{len(groups)} group(s); a function with no twin is not "
                             f"reported")
    return t


if __name__ == "__main__":
    main(build, __file__)

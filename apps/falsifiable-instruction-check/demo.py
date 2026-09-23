"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from falsifiable import Candidate, Registry, register  # noqa: E402

VIOLATING = "result = eval(user_input)\n"
SATISFYING = "result = int(user_input)\n"

SOUND = Candidate(
    id="INS-010",
    text="Generated modules must not call eval()",
    check=lambda source: "eval(" not in source,
    violating=VIOLATING,
    satisfying=SATISFYING,
)


def candidate(id, check):
    return Candidate(id, "Generated modules must not call eval()", check,
                     violating=VIOLATING, satisfying=SATISFYING)


def build() -> Trace:
    t = Trace(
        app="falsifiable-instruction-check",
        claim=(
            "An instruction registers only if its own checker rejects the violating "
            "fixture it ships and accepts the satisfying one — a checker that cannot "
            "discriminate between them is refused."
        ),
        enforcement="deterministic",
        denial_type="NotFalsifiable",
    )
    t.allow(
        "a checker that tells the two fixtures apart",
        {"instruction": "must not call eval()",
         "violating": VIOLATING.strip(), "satisfying": SATISFYING.strip()},
        lambda: f"registered {register(SOUND).id}",
        evidence=lambda: "the fixtures stay attached, so the claim can be re-verified "
                         "rather than trusted",
    )
    t.deny(
        "a checker that passes everything",
        {"check": "lambda source: True", "violating": VIOLATING.strip()},
        lambda: register(candidate("INS-011", lambda source: True)),
        note="A policy full of checkers that never fire reports total compliance and "
             "means nothing.",
    )
    t.deny(
        "a checker that fails everything",
        {"check": "lambda source: False", "satisfying": SATISFYING.strip()},
        lambda: register(candidate("INS-012", lambda source: False)),
        note="Not vacuous, useless in the other direction: it would fail every "
             "artifact and be switched off within a day.",
    )
    t.deny(
        "a checker looking for the wrong string",
        {"instruction": "must not call eval()",
         "check": "'evaluate(' not in source"},
        lambda: register(candidate("INS-013", lambda source: "evaluate(" not in source)),
        evidence=lambda: "reads correctly, matches nothing",
        note="The real shape of this bug. Without a violating fixture it passes every "
             "artifact forever, silently, and looks exactly like a checker that works.",
    )
    t.deny(
        "an instruction shipped without a violating fixture",
        {"violating": "(none)", "satisfying": SATISFYING.strip()},
        lambda: register(Candidate("INS-014", "must not call eval()",
                                   lambda s: "eval(" not in s, satisfying=SATISFYING)),
        note="Without one there is no way to tell a strict checker from a stub.",
    )
    t.deny(
        "a checker that raises on its own fixture",
        {"check": "raises RuntimeError"},
        lambda: register(candidate("INS-016",
                                   lambda s: (_ for _ in ()).throw(RuntimeError("bug")))),
    )
    registry = Registry()
    registry.add(SOUND)
    t.allow(
        "what a registry ends up holding",
        {"offered": "INS-010 (sound), INS-011 (vacuous)"},
        lambda: list(registry.ids()),
        evidence=lambda: "only the falsifiable one was admitted",
    )
    return t


if __name__ == "__main__":
    main(build, __file__)

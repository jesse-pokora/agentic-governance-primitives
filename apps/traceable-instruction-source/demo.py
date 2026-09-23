"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from anchor import Anchor, anchor, resolve  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

ORIGINAL = {
    "AGENTS.md": [
        "# Toy agent instructions",
        "",
        "## Architecture",
        "Constructors receive their collaborators.",
        "Collaborators are built in the composition root.",
        "",
        "## Output",
        "Return Markdown only.",
    ]
}


def variant(**changes):
    lines = list(ORIGINAL["AGENTS.md"])
    for index, text in changes.items():
        lines[int(index)] = text
    return {"AGENTS.md": lines}


def build() -> Trace:
    anchored = anchor(ORIGINAL, "AGENTS.md", 4, 5)

    t = Trace(
        app="traceable-instruction-source",
        claim=(
            "An instruction is bound to the exact text at an exact location; if the "
            "source no longer contains that text, resolving it is refused rather than "
            "silently re-read from whatever now sits at those lines."
        ),
        enforcement="deterministic",
        denial_type="StaleInstruction",
    )
    t.allow("the source is unchanged",
            {"anchor": "AGENTS.md:4-5", "digest": anchored.digest[:16] + "..."},
            lambda: resolve(anchored, ORIGINAL).replace("\n", " / "),
            evidence=lambda: "text and digest both match")
    t.deny("the instruction itself was edited",
           {"anchor": "AGENTS.md:4-5",
            "line 4 now": "Constructors may build their collaborators."},
           lambda: resolve(anchored, variant(**{"3": "Constructors may build their collaborators."})),
           note="'receive' became 'may build' — the criterion id and the citation both "
                "survive an edit like this. Only the meaning changes.")
    t.deny("a paragraph was inserted above it",
           {"anchor": "AGENTS.md:4-5", "change": "one line added at the top"},
           lambda: resolve(anchored, {"AGENTS.md": ["## Preamble"] + list(ORIGINAL["AGENTS.md"])}),
           evidence=lambda: "lines 4-5 now hold different text",
           note="The trap. Without the quoted text this still resolves cleanly, still "
                "returns something, and now points at somebody else's words.")
    t.deny("trailing whitespace was added",
           {"anchor": "AGENTS.md:4-5", "change": "two spaces at the end of line 4"},
           lambda: resolve(anchored, variant(**{"3": "Constructors receive their collaborators.  "})),
           note="Comparison is exact. An exact gate can be loosened deliberately; a "
                "fuzzy one cannot be tightened back with confidence.")
    t.deny("the file was truncated",
           {"anchor": "AGENTS.md:4-5", "file now": "3 lines"},
           lambda: resolve(anchored, {"AGENTS.md": ORIGINAL["AGENTS.md"][:3]}))
    t.deny("the anchor's own digest was tampered with",
           {"quoted text": "unchanged", "recorded digest": "ffff...ffff"},
           lambda: resolve(Anchor(anchored.path, 4, 5, anchored.quoted, "f" * 64), ORIGINAL),
           evidence=lambda: "the quote matched; the anchor did not")
    t.allow("an unrelated edit elsewhere in the file",
            {"anchor": "AGENTS.md:4-5", "change": "line 8 reworded"},
            lambda: resolve(anchored, variant(**{"7": "Return Markdown only, and nothing else."})).replace("\n", " / "),
            note="A rule that cried wolf on every unrelated change would be switched "
                 "off within a week.")
    return t


if __name__ == "__main__":
    main(build, __file__)

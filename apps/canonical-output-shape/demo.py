"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from output_shape import verify_shape  # noqa: E402

GOOD = ("# Repository Guide\n\nA toy repository.\n\n## Purpose\n\nDemonstrates one "
        "governance primitive.\n\n## Key Paths\n\n- `apps/` one directory per app\n")


def build() -> Trace:
    t = Trace(
        app="canonical-output-shape",
        claim=(
            "Generated output is accepted only if its headings are canonical, spelled "
            "exactly and in the declared order, with no wrapper fence, no empty section, "
            "and no more than the declared word bound — and the checker never repairs "
            "what it rejects."
        ),
        enforcement="deterministic",
        denial_type="OutputShapeRejected",
    )
    t.allow("a conforming document that omits two optional sections",
            {"headings": "# Repository Guide, ## Purpose, ## Key Paths",
             "omitted": "## Architecture, ## Build and Test"},
            lambda: verify_shape(GOOD).headings,
            evidence=lambda: "omitting a section the evidence did not support is correct")
    t.deny("a heading with nothing under it",
           {"added": "## Build and Test (empty)"},
           lambda: verify_shape(GOOD + "\n## Build and Test\n\n"),
           note="An empty heading reads as an answer and is not one.")
    t.deny("a canonical heading spelled slightly wrong",
           {"emitted": "## Key paths", "canonical": "## Key Paths"},
           lambda: verify_shape(GOOD.replace("## Key Paths", "## Key paths")))
    t.deny("a heading with no space after the hashes",
           {"emitted": "##Key Paths"},
           lambda: verify_shape(GOOD.replace("## Key Paths", "##Key Paths")),
           note="Not an ATX heading at all — Markdown renders it as body text. It "
                "would sail past a canonical-heading check while looking to a human "
                "like a section that is present.")
    t.deny("canonical sections in the wrong order",
           {"emitted": "# Repository Guide, ## Key Paths, ## Purpose"},
           lambda: verify_shape("# Repository Guide\n\nintro\n\n## Key Paths\n\n- a\n\n"
                                "## Purpose\n\nwhy\n"))
    t.deny("the whole document wrapped in a code fence",
           {"emitted": "```markdown ... ```"},
           lambda: verify_shape("```markdown\n" + GOOD + "```\n"))
    t.allow("a fenced block inside a section",
            {"section": "## Build and Test", "contains": "```bash ... ```"},
            lambda: verify_shape(GOOD + "\n## Build and Test\n\n```bash\npython -m unittest\n```\n").headings,
            note="A fence inside a section is content; a fence around the document is "
                 "a wrapper. Only the second is rejected.")
    t.deny("output over the declared word bound",
           {"words": "over 200", "max_words": 50},
           lambda: verify_shape(GOOD + "\n## Build and Test\n\n" + ("word " * 200),
                                max_words=50))
    return t


if __name__ == "__main__":
    main(build, __file__)

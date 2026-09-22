"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from managed_block import END_MARKER, START_MARKER, write_managed_block  # noqa: E402

ABOVE = "# Toy Repository\r\n\r\nHand-written by a person.   \r\n"
BELOW = "\r\n## Notes\r\n\tstill hand-written\r\n"


def build() -> Trace:
    tmp = tempfile.mkdtemp(prefix="demo-mbc-")
    path = os.path.join(tmp, "AGENTS.md")
    seed = lambda text: Path(path).write_text(text, encoding="utf-8", newline="")  # noqa: E731
    seed(f"{ABOVE}{START_MARKER}\ngenerated v1\n{END_MARKER}{BELOW}")

    t = Trace(
        app="managed-block-confinement",
        claim=(
            "A managed write replaces only the content between the exact markers — "
            "everything outside them survives byte for byte, and generated content "
            "carrying a marker of its own is refused rather than written."
        ),
        enforcement="deterministic",
        denial_type="ManagedWriteDenied",
        redactions={tmp: "<tmp>", tmp.replace("\\", "/"): "<tmp>"},
    )
    t.allow("the agent rewrites its own block",
            {"document": "human text + managed block + human text",
             "new content": "generated v2"},
            lambda: write_managed_block(path, "generated v2").replace("\r\n", "\r\n"),
            evidence=lambda: "text above and below the markers is the original bytes, "
                             "CRLF endings and trailing spaces included",
            note="Rewriting the whole file is the usual approach, and it silently "
                 "normalizes exactly this.")
    t.deny("generated content carrying a start marker",
           {"new content": f"sneaky\n{START_MARKER}\nsecond block"},
           lambda: write_managed_block(path, f"sneaky\n{START_MARKER}\nsecond block"),
           evidence=lambda: "the file was never opened — the render is pure and "
                            "refused first",
           note="Two start markers means no single managed region, and every later "
                "edit would have to guess which one the agent owns.")
    t.deny("generated content carrying an end marker",
           {"new content": f"{END_MARKER}\nand then text pretending to be human"},
           lambda: write_managed_block(path, f"{END_MARKER}\nand then human text"),
           note="The inverse trick: escape the block and write below it.")

    seed(f"{START_MARKER}\na\n{END_MARKER}\n{START_MARKER}\nb\n{END_MARKER}\n")
    t.deny("a document that already contains two blocks",
           {"document": "two managed blocks", "new content": "which one is mine?"},
           lambda: write_managed_block(path, "v2"),
           note="Ambiguity fails closed. Absence does not — a document with no block "
                "yet is legal, and the block is created without moving anything.")

    seed(ABOVE)
    t.allow("creating the block for the first time",
            {"document": "human text only, no markers", "new content": "first generation"},
            lambda: write_managed_block(path, "first generation").replace("\r\n", "\r\n"),
            evidence=lambda: f"exactly one block; temp files left behind: "
                             f"{[f for f in os.listdir(tmp) if f != 'AGENTS.md']}")
    t.allow("writing the same content a second time",
            {"new content": "first generation", "call": "2nd"},
            lambda: "identical document, still exactly one block"
                    if write_managed_block(path, "first generation")
                    == write_managed_block(path, "first generation") else "differed",
            note="A re-run is a no-op, not a slow accumulation of blocks.")
    return t


if __name__ == "__main__":
    main(build, __file__)

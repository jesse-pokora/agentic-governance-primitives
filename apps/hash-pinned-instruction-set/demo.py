"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from instruction_set import (  # noqa: E402
    InstructionManifest, PinnedInstructionSet, run_under, verify,
)

AGENTS = b"# toy agent instructions\nalways state the atomic claim\n"
REVIEW = b"# toy review instructions\nreject findings without evidence\n"


def build() -> Trace:
    files = {"AGENTS.md": AGENTS, "REVIEW.md": REVIEW}
    pinned = PinnedInstructionSet.pin(InstructionManifest.from_files(files))
    ran = []

    t = Trace(
        app="hash-pinned-instruction-set",
        claim=(
            "A run executes only under the exact instruction set it pinned — a single "
            "edited byte, an added file, a removed file, or two files swapping contents "
            "all fail closed before the run starts."
        ),
        enforcement="deterministic",
        denial_type="InstructionDrift",
    )
    t.allow("the instruction set is byte-for-byte the pinned one",
            {"files": "AGENTS.md, REVIEW.md", "manifest": pinned.manifest_digest[:16] + "..."},
            lambda: run_under(pinned, InstructionManifest.from_files(dict(files)),
                              lambda: ran.append(1) or "executed"),
            evidence=lambda: f"run executed: {len(ran)} time")

    edited = dict(files, **{"AGENTS.md": AGENTS.replace(b"always", b"rarely")})
    t.deny("one word changed in one instruction file",
           {"files": "AGENTS.md (edited), REVIEW.md",
            "manifest": InstructionManifest.from_files(edited).digest[:16] + "..."},
           lambda: run_under(pinned, InstructionManifest.from_files(edited),
                             lambda: ran.append(1)),
           evidence=lambda: f"run executed: {len(ran)} time — unchanged",
           note="Drift is caught before the run starts, not noticed in the audit after.")

    t.deny("an extra instruction file the pinned run never saw",
           {"files": "AGENTS.md, REVIEW.md, SHADOW.md"},
           lambda: verify(pinned, InstructionManifest.from_files(
               dict(files, **{"SHADOW.md": b"# injected\n"}))),
           note="Re-hashing only known files would accept an injected one silently.")

    t.deny("the same two files, contents swapped between them",
           {"AGENTS.md": "now holds REVIEW.md's bytes",
            "REVIEW.md": "now holds AGENTS.md's bytes"},
           lambda: verify(pinned, InstructionManifest.from_files(
               {"AGENTS.md": REVIEW, "REVIEW.md": AGENTS})),
           note="The multiset of hashes is identical. Only the name-to-hash binding "
                "moved, and that is what the manifest binds.")
    return t


if __name__ == "__main__":
    main(build, __file__)

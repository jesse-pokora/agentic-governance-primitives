"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from confined_writer import ConfinedWriter  # noqa: E402
from demo_trace import Trace, main  # noqa: E402


def build() -> Trace:
    tmp = tempfile.mkdtemp(prefix="demo-wsc-")
    root = os.path.join(tmp, "work")
    outside = os.path.join(tmp, "outside")
    sibling = os.path.join(tmp, "work-evil")
    for p in (root, outside, sibling):
        os.makedirs(p)
    writer = ConfinedWriter(root)
    stolen = os.path.join(outside, "stolen.txt")

    t = Trace(
        app="write-scope-confinement",
        claim=(
            "A write is denied before any bytes touch disk unless its fully resolved path "
            "lies inside the declared scope root — traversal, absolute paths, prefix "
            "siblings, and symlink escapes all fail closed."
        ),
        enforcement="deterministic",
        denial_type="WriteDenied",
        redactions={tmp: "<tmp>", tmp.replace("\\", "/"): "<tmp>"},
    )
    t.allow("a path inside the scope root",
            {"scope root": "<tmp>/work", "path": "notes/toy.txt"},
            lambda: writer.write("notes/toy.txt", b"toy payload"),
            evidence=lambda: "file written, parent directory created inside the scope")
    t.deny("parent traversal out of the scope",
           {"scope root": "<tmp>/work", "path": "../outside/stolen.txt"},
           lambda: writer.write(os.path.join("..", "outside", "stolen.txt"), b"nope"),
           evidence=lambda: f"target exists afterwards: {os.path.exists(stolen)}")
    t.deny("an absolute path outside the scope",
           {"scope root": "<tmp>/work", "path": "<tmp>/outside/stolen.txt"},
           lambda: writer.write(stolen, b"nope"),
           evidence=lambda: f"target exists afterwards: {os.path.exists(stolen)}")
    t.deny("a sibling directory whose name has the root as a string prefix",
           {"scope root": "<tmp>/work", "path": "<tmp>/work-evil/stolen.txt"},
           lambda: writer.write(os.path.join(sibling, "stolen.txt"), b"nope"),
           note="A startswith() containment check allows this write. Containment is "
                "compared component-wise instead.")

    link = os.path.join(root, "escape_hatch")
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        return t
    t.deny("a symlink inside the scope pointing out of it",
           {"scope root": "<tmp>/work", "path": "escape_hatch/stolen.txt",
            "resolves to": "<tmp>/outside/stolen.txt"},
           lambda: writer.write(os.path.join("escape_hatch", "stolen.txt"), b"nope"),
           evidence=lambda: f"target exists afterwards: {os.path.exists(stolen)}",
           note="Looks inside lexically; resolves outside. Both paths are compared.")
    return t


if __name__ == "__main__":
    main(build, __file__)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from attestation import attest, init_snapshot_repo  # noqa: E402
from demo_trace import Trace, main  # noqa: E402


def build() -> Trace:
    repo = tempfile.mkdtemp(prefix="demo-wa-")
    init_snapshot_repo(repo)
    write = lambda name, body: Path(repo, name).write_text(body, encoding="utf-8")  # noqa: E731

    t = Trace(
        app="workspace-attestation",
        claim=(
            "A governed run's claimed file changes are diffed against a real git-worktree "
            "snapshot taken immediately before and after — a claim that doesn't match the "
            "diff fails closed."
        ),
        enforcement="deterministic",
        denial_type="AttestationMismatch",
        redactions={repo: "<repo>", repo.replace("\\", "/"): "<repo>"},
    )
    write("new_toy.txt", "added by the run\n")
    t.allow("the run claims exactly what it did",
            {"claimed added": "new_toy.txt", "claimed modified": "(none)",
             "claimed deleted": "(none)"},
            lambda: attest(repo, ["new_toy.txt"], [], []),
            evidence=lambda: "claim and real git diff are identical")

    write("second_toy.txt", "also added, but not mentioned\n")
    t.deny("the run made a change it did not claim",
           {"claimed added": "new_toy.txt", "actually added": "new_toy.txt, second_toy.txt"},
           lambda: attest(repo, ["new_toy.txt"], [], []),
           note="The most consequential shape: an unreported write. An honest-looking "
                "claim that is merely incomplete still fails closed.")

    t.deny("the run claims a change that never happened",
           {"claimed added": "new_toy.txt, second_toy.txt, imaginary.txt",
            "actually added": "new_toy.txt, second_toy.txt"},
           lambda: attest(repo, ["new_toy.txt", "second_toy.txt", "imaginary.txt"], [], []),
           evidence=lambda: "the diff is the ground truth, not the claim",
           note="A claim is not evidence of work. It is the thing being checked.")
    return t


if __name__ == "__main__":
    main(build, __file__)

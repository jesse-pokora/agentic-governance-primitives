"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from separation import Approval, Artifact, accept  # noqa: E402

CONTENT = {"guide": "toy repository guide", "version": 1}
REVISED = {"guide": "toy repository guide, revised", "version": 2}


def build() -> Trace:
    artifact = Artifact(produced_by="toy-writer-agent", content=CONTENT)
    digest = artifact.digest
    t = Trace(
        app="producer-approver-separation",
        claim=(
            "Whoever produced an artifact cannot approve it, and an approval is bound to "
            "the exact digest it covers — a rename, a delegate, or a later edit all fail "
            "closed."
        ),
        enforcement="deterministic",
        denial_type="ApprovalDenied",
    )
    t.allow("an independent approver naming the exact digest",
            {"produced_by": "toy-writer-agent", "approved_by": "toy-human-reviewer",
             "digest": digest[:20] + "..."},
            lambda: accept(artifact, Approval("toy-human-reviewer", digest)).approved_by)
    t.deny("the producer approving its own artifact",
           {"produced_by": "toy-writer-agent", "approved_by": "toy-writer-agent"},
           lambda: accept(artifact, Approval("toy-writer-agent", digest)))
    t.deny("the same actor, respelled",
           {"produced_by": "toy-writer-agent", "approved_by": "  TOY-Writer-Agent  "},
           lambda: accept(artifact, Approval("  TOY-Writer-Agent  ", digest)),
           note="An independence check that a respelling defeats is decorative.")
    t.deny("the producer approving through a service account",
           {"approved_by": "ci-service-account",
            "delegates": "ci-service-account -> toy-writer-agent"},
           lambda: accept(artifact, Approval("ci-service-account", digest),
                          delegates={"ci-service-account": "toy-writer-agent"}),
           note="The realistic shape: nobody types their own name in the approver "
                "field, they configure CI to do it.")
    t.deny("an approval that named a different artifact",
           {"approves": Artifact("toy-writer-agent", REVISED).digest[:20] + "...",
            "artifact": digest[:20] + "..."},
           lambda: accept(artifact, Approval("toy-human-reviewer",
                                             Artifact("toy-writer-agent", REVISED).digest)))
    t.deny("the artifact edited after it was approved",
           {"approved digest": digest[:20] + "...",
            "artifact now": Artifact("toy-writer-agent", REVISED).digest[:20] + "..."},
           lambda: accept(Artifact("toy-writer-agent", REVISED),
                          Approval("toy-human-reviewer", digest)),
           note="An approval that survives an edit is a signature on a document nobody "
                "read.")
    t.allow("a delegate acting for someone genuinely independent",
            {"approved_by": "ci-service-account",
             "delegates": "ci-service-account -> toy-human-reviewer"},
            lambda: accept(artifact, Approval("ci-service-account", digest),
                           delegates={"ci-service-account": "toy-human-reviewer"}).approved_by)
    return t


if __name__ == "__main__":
    main(build, __file__)

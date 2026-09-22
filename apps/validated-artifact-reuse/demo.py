"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from reuse import Artifact, digest_of, obtain  # noqa: E402

INPUTS = {"repo": "toy-repo", "files": ["a.py", "b.py"]}
CHANGED = {"repo": "toy-repo", "files": ["a.py", "b.py", "c.py"]}
VERSION = "summarizer-2.1.0"


class ProducerSpy:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return "freshly generated guide"


def existing(inputs=INPUTS, version=VERSION, generation=3):
    return Artifact("existing guide", digest_of(inputs), version, generation)


def build() -> Trace:
    t = Trace(
        app="validated-artifact-reuse",
        claim=(
            "An existing artifact is reused only when it is still valid for the inputs "
            "at hand — same input digest and same producer version — and every decision "
            "records which way it went and why."
        ),
        enforcement="deterministic",
        denial_type="n/a — this app returns a Decision, it does not raise",
    )

    def step(label, request, artifact, inputs, version, note="", evidence=None):
        spy = ProducerSpy()
        decision = obtain(artifact, inputs, version, spy)
        t.verdict(label, request, lambda: decision, lambda d: d.reused,
                  lambda d: d.reason,
                  evidence=(evidence or (lambda: f"producer invoked {spy.calls} time(s); "
                                                 f"generation {decision.artifact.generation}")),
                  note=note)

    step("the inputs and producer version are unchanged",
         {"input digest": digest_of(INPUTS)[:20] + "...", "producer": VERSION},
         existing(), INPUTS, VERSION,
         note="Validity is checked against what the artifact was made from, never "
              "against when it was made.")
    step("one file was added to the inputs",
         {"was": "a.py, b.py", "now": "a.py, b.py, c.py"},
         existing(), CHANGED, VERSION,
         note="The failure that matters is not a slow rebuild. It is a fast, confident "
              "answer computed from inputs that have since changed.")
    step("the producer was upgraded",
         {"artifact built by": VERSION, "producer now": "summarizer-3.0.0"},
         existing(), INPUTS, "summarizer-3.0.0")
    step("no artifact exists yet",
         {"existing": "none"}, None, INPUTS, VERSION)
    step("the stored digest is not a well-formed SHA-256",
         {"stored digest": "not-a-digest"},
         Artifact("stale", "not-a-digest", VERSION, 1), INPUTS, VERSION,
         note="An untrustworthy record is not a reason to skip work.")
    step("the same inputs, built as a dict in a different order",
         {"inputs": '{"files": [...], "repo": "toy-repo"}'},
         existing(), {"files": ["a.py", "b.py"], "repo": "toy-repo"}, VERSION,
         note="Digests are taken over canonical JSON, so key order is not a change.")
    step("the same files, listed in a different order",
         {"was": '["a.py", "b.py"]', "now": '["b.py", "a.py"]'},
         existing(), {"repo": "toy-repo", "files": ["b.py", "a.py"]}, VERSION,
         note="A list is ordered data, not a set. Treating the two as equal would be a "
              "guess about what the list means.")
    return t


if __name__ == "__main__":
    main(build, __file__)

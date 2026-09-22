"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from agent_message import Message, Recipient, sign  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

PLANNER_KEY, AUDITOR_KEY = b"toy-planner-key", b"toy-auditor-key"
TASK = {"task": "summarize svc-fake-a"}


def build() -> Trace:
    worker = Recipient(
        "worker-agent", {"planner-agent": PLANNER_KEY, "auditor-agent": AUDITOR_KEY}
    )
    good = sign(Message("planner-agent", "worker-agent", 1, TASK), PLANNER_KEY)

    t = Trace(
        app="authenticated-agent-message",
        claim=(
            "A message between agents is accepted only if it is signed by a sender the "
            "recipient knows, addressed to that recipient, and carries a sequence number "
            "strictly greater than the last one accepted from that sender."
        ),
        enforcement="deterministic",
        denial_type="MessageRejected",
    )
    t.allow(
        "signed by a known sender, addressed here, sequence 1",
        {"from": "planner-agent", "to": "worker-agent", "sequence": 1},
        lambda: worker.accept(good),
        evidence=lambda: "signature covers sender, recipient, sequence and payload",
    )
    t.deny(
        "the same message delivered a second time",
        {"from": "planner-agent", "to": "worker-agent", "sequence": 1,
         "last accepted": 1},
        lambda: worker.accept(good),
        note="A replay is a message that was genuine once. A signature check alone "
             "cannot see it.",
    )
    t.deny(
        "a payload edited after signing",
        {"payload was": "summarize svc-fake-a", "payload now": "delete svc-fake-a"},
        lambda: worker.accept(
            Message("planner-agent", "worker-agent", 2,
                    {"task": "delete svc-fake-a"}, good.signature)
        ),
    )
    t.deny(
        "a genuine message addressed to a different agent",
        {"from": "planner-agent", "to": "auditor-agent", "I am": "worker-agent"},
        lambda: worker.accept(
            sign(Message("planner-agent", "auditor-agent", 2, TASK), PLANNER_KEY)
        ),
        note="Signed, genuine, and not for me. Acting on it is the agentic equivalent "
             "of opening someone else's post.",
    )
    intercepted = sign(Message("planner-agent", "auditor-agent", 3, TASK), PLANNER_KEY)
    t.deny(
        "that intercepted message re-addressed to me",
        {"was addressed to": "auditor-agent", "now claims": "worker-agent",
         "signature": "unchanged"},
        lambda: worker.accept(
            Message("planner-agent", "worker-agent", 3, TASK, intercepted.signature)
        ),
        evidence=lambda: "fails as signature_invalid, because the recipient is signed "
                         "too",
        note="This is why the signature covers every field the recipient will act on, "
             "not just the payload.",
    )
    t.deny(
        "a message from an agent whose key I do not hold",
        {"from": "rogue-agent", "keys held": "planner-agent, auditor-agent"},
        lambda: worker.accept(
            sign(Message("rogue-agent", "worker-agent", 1, TASK), b"rogue-key")
        ),
    )
    t.allow(
        "a gap in the sequence, after a dropped message",
        {"from": "planner-agent", "sequence": 9, "last accepted": 1},
        lambda: worker.accept(
            sign(Message("planner-agent", "worker-agent", 9, TASK), PLANNER_KEY)
        ),
        note="Refusing to move past a gap would let one lost message wedge the channel "
             "forever. What is refused is a sequence already seen.",
    )
    return t


if __name__ == "__main__":
    main(build, __file__)

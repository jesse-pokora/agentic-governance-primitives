"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from delegation import Grant, effective_authority, may  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

ROOT = Grant.of("orchestrator", {"repo.read", "repo.write", "deploy.execute"})


def build() -> Trace:
    t = Trace(
        app="delegation-scope-attenuation",
        claim=(
            "Authority can only shrink as it is delegated — each link in a chain may "
            "hold a subset of what the link before it held, never a capability its "
            "delegator did not have."
        ),
        enforcement="deterministic",
        denial_type="DelegationDenied",
    )
    attenuating = [
        ROOT,
        Grant.of("planner-agent", {"repo.read", "repo.write"}),
        Grant.of("worker-agent", {"repo.read"}),
    ]
    t.allow(
        "a chain that narrows at every link",
        {"orchestrator": "repo.read, repo.write, deploy.execute",
         "planner-agent": "repo.read, repo.write",
         "worker-agent": "repo.read"},
        lambda: sorted(effective_authority(attenuating)),
        evidence=lambda: f"may read: {may(attenuating, 'repo.read')}; "
                         f"may write: {may(attenuating, 'repo.write')}",
    )
    t.deny(
        "a sub-agent claiming more than its delegator held",
        {"planner-agent": "repo.read", "worker-agent": "repo.read, deploy.execute"},
        lambda: effective_authority([
            ROOT,
            Grant.of("planner-agent", {"repo.read"}),
            Grant.of("worker-agent", {"repo.read", "deploy.execute"}),
        ]),
        note="Without this rule, delegation is a laundering step: the sub-agent asks "
             "for more than its delegator could have, and nothing downstream can tell "
             "the difference.",
    )
    t.deny(
        "a capability re-acquired four links down",
        {"chain": "orchestrator -> a -> b -> c -> d", "d re-claims": "repo.write"},
        lambda: effective_authority([
            ROOT,
            Grant.of("a", {"repo.read", "repo.write"}),
            Grant.of("b", {"repo.read"}),
            Grant.of("c", {"repo.read"}),
            Grant.of("d", {"repo.read", "repo.write"}),
        ]),
        evidence=lambda: "the denial names the capability and the depth",
    )
    t.deny(
        "a loop back to an earlier actor",
        {"chain": "orchestrator -> planner-agent -> orchestrator"},
        lambda: effective_authority([
            ROOT,
            Grant.of("planner-agent", {"repo.read"}),
            Grant.of("orchestrator", {"repo.read"}),
        ]),
        note="A loop lets authority be re-derived from a later link, which is "
             "amplification wearing a longer path.",
    )
    t.deny(
        "a near-miss capability name",
        {"root holds": "repo.read", "sub claims": "repo.read_secrets"},
        lambda: effective_authority([
            Grant.of("root", {"repo.read"}),
            Grant.of("sub", {"repo.read_secrets"}),
        ]),
        note="Names are compared exactly. A gate that read structure into them would "
             "turn every new capability name into a silent policy change.",
    )
    t.allow(
        "delegating the work while delegating no authority",
        {"orchestrator": "repo.read, repo.write, deploy.execute",
         "planner-agent": "(nothing)"},
        lambda: sorted(effective_authority([ROOT, Grant.of("planner-agent", set())]))
                or "empty set",
        note="A correct answer, not an error: an agent may be asked to do something "
             "and given no authority to act on its own.",
    )
    return t


if __name__ == "__main__":
    main(build, __file__)

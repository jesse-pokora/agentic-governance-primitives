"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from dry_run import Executor, PlannedEffect  # noqa: E402


def do_work(executor, guide, index):
    """One routine, both modes. There is no dry-run branch in here."""
    executor.perform(PlannedEffect("write", guide, "managed guide, 3 sections"),
                     lambda: Path(guide).write_text("generated guide\n", encoding="utf-8"))
    executor.perform(PlannedEffect("write", index, "index entry"),
                     lambda: Path(index).write_text("toy index\n", encoding="utf-8"))
    return executor.plan


def build() -> Trace:
    tmp = tempfile.mkdtemp(prefix="demo-pdr-")
    guide, index = os.path.join(tmp, "AGENTS.md"), os.path.join(tmp, "INDEX.md")

    t = Trace(
        app="provable-dry-run",
        claim=(
            "A dry run performs no effect and still produces the complete plan — and the "
            "plan a dry run produces is the same plan the live run produces, because "
            "both execute the same routine."
        ),
        enforcement="deterministic",
        denial_type="EffectDenied",
        # The escaped spelling first: results are JSON-serialized before
        # redaction runs, so backslashes arrive doubled.
        redactions={
            tmp.replace("\\", "\\\\"): "<tmp>",
            tmp.replace("\\", "/"): "<tmp>",
            tmp: "<tmp>",
        },
    )
    dry = Executor(dry_run=True)
    t.allow("a dry run over two writes",
            {"mode": "dry_run=True", "effects": "write AGENTS.md, write INDEX.md"},
            lambda: do_work(dry, guide, index),
            evidence=lambda: f"files on disk: {sorted(os.listdir(tmp))}; effects performed: "
                             f"{len(dry.performed)}")
    live = Executor(dry_run=False)
    t.allow("the same routine, live",
            {"mode": "dry_run=False", "effects": "write AGENTS.md, write INDEX.md"},
            lambda: do_work(live, guide, index),
            evidence=lambda: f"files on disk: {sorted(os.listdir(tmp))}; effects "
                             f"performed: {len(live.performed)}")
    t.allow("the dry plan and the live plan are the same plan",
            {"dry plan": "2 effects", "live plan": "2 effects"},
            lambda: "identical" if dry.plan == live.plan else "DIFFERENT",
            evidence=lambda: "both modes ran the same routine, with no dry-run branch "
                             "inside it",
            note="A dry run you cannot trust to describe the real run is worse than no "
                 "dry run, because it is reassuring.")
    t.deny("an effect with no target, in either mode",
           {"effect": 'kind="write", target=""'},
           lambda: Executor(dry_run=True).perform(PlannedEffect("write", "", "no target"),
                                                  lambda: None))
    t.allow("a write that bypassed the gate entirely",
            {"call": 'Path(...).write_text(...) directly', "executor": "not consulted"},
            lambda: (Path(os.path.join(tmp, "SNEAKY.md"))
                     .write_text("written without asking\n", encoding="utf-8")
                     and None) or f"planned effects recorded: {len(Executor(dry_run=True).planned)}",
            evidence=lambda: "the executor neither knows nor reports it",
            note="Stated as a step so the limitation is on the record: this proves "
                 "effects routed through the gate are suppressed, not that nothing "
                 "else in a codebase writes directly.")
    return t


if __name__ == "__main__":
    main(build, __file__)

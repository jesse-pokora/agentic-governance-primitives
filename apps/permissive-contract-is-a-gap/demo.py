"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from contract_gap import Rule, audit, gaps, string_schema  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

NON_EMPTY = Rule("RS-109", "A prompt must be a string of at least one character",
                 forbidden_examples=("", 123, None))
NOT_WHITESPACE = Rule("RS-111", "A prompt must carry content, not only whitespace",
                      forbidden_examples=("   ", "\t", "\n"))
RULES = [NON_EMPTY, NOT_WHITESPACE]
REAL_TRAFFIC = ["summarize the repo", "list the toy paths", "explain the tests"]


def build() -> Trace:
    t = Trace(
        app="permissive-contract-is-a-gap",
        claim=(
            "If a contract admits a value the instruction forbids, that is a gap — "
            "recorded even when no artifact has ever sent such a value."
        ),
        enforcement="deterministic",
        denial_type="ContractRejected",
    )
    strict = string_schema(min_length=1, pattern=r"\S.*")
    t.allow(
        "a contract that rejects every forbidden value",
        {"contract": "string, min length 1, must contain non-whitespace",
         "rules": "RS-109, RS-111"},
        lambda: [f"{f.rule_id}: {f.status}" for f in audit(strict, RULES)],
    )
    loose = string_schema(min_length=1)
    findings = audit(loose, RULES)
    t.allow(
        "a contract that only checks length",
        {"contract": "string, min length 1", "rules": "RS-109, RS-111"},
        lambda: [f"{f.rule_id}: {f.status}" for f in findings],
        evidence=lambda: f"admitted by the contract: "
                         f"{', '.join(gaps(findings)[0].admitted)}",
        note="RS-109 holds because the empty string is rejected. RS-111 does not, "
             "because whitespace sails through — and nothing about today's traffic "
             "would tell you that.",
    )
    permissive = string_schema(min_length=0)
    t.allow(
        "every real value passes, and the gap is reported anyway",
        {"contract": "string, any length",
         "real traffic": ", ".join(repr(v) for v in REAL_TRAFFIC)},
        lambda: (f"all real traffic accepted: "
                 f"{all(permissive(v) for v in REAL_TRAFFIC)}; "
                 f"gaps: {[g.rule_id for g in gaps(audit(permissive, RULES))]}"),
        evidence=lambda: "the audit takes a contract and rules — there is nowhere to "
                         "pass a sample",
        note="The most comfortable failure there is. Every sample passes, every test "
             "is green, and the only thing holding the line is that nobody has yet "
             "sent the empty string the schema has always accepted.",
    )
    t.deny(
        "a rule that forbids nothing",
        {"rule": "RS-000 'be sensible'", "forbidden examples": "(none)"},
        lambda: Rule("RS-000", "be sensible", forbidden_examples=()),
        note="It cannot be violated, so a contract cannot fail it, so declaring it "
             "proves nothing.",
    )
    t.deny(
        "auditing a contract against no rules at all",
        {"contract": "string, min length 1", "rules": "(none)"},
        lambda: audit(strict, []),
    )
    return t


if __name__ == "__main__":
    main(build, __file__)

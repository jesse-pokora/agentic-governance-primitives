"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from environment import EnvironmentPolicy, build_child_environment, run  # noqa: E402

DUMP = "import os, json; print(json.dumps(sorted(os.environ)))"
PARENT = {
    "PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    "MODEL_ENDPOINT": "https://api.example.test",
    "AWS_SECRET_ACCESS_KEY": "toy-secret-AAAA1111",
    "GITHUB_TOKEN": "toy-ghp-BBBB2222",
    "OPERATOR_SSH_KEY": "-----BEGIN PRIVATE KEY-----",
    "SOME_FUTURE_SECRET": "nobody wrote a rule for this one",
}
POLICY = EnvironmentPolicy.of(passthrough={"MODEL_ENDPOINT"})


def build() -> Trace:
    t = Trace(
        app="reduced-child-environment",
        claim=(
            "A child process receives only the variables a declared policy passes "
            "through — every other variable in the parent's environment, including ones "
            "nobody anticipated, is absent rather than redacted."
        ),
        enforcement="deterministic",
        denial_type="EnvironmentDenied",
        redactions={os.environ.get("PATH", "\x00"): "<PATH>",
                    sys.executable: "<python>"},
    )
    t.allow("building the child environment from an allowlist",
            {"parent holds": ", ".join(sorted(PARENT)), "passthrough": "MODEL_ENDPOINT"},
            lambda: sorted(build_child_environment(PARENT, POLICY)),
            evidence=lambda: "built up from {} rather than filtered down from the parent")
    t.allow("a secret nobody wrote a rule for",
            {"variable": "SOME_FUTURE_SECRET", "policy mentions it": "no"},
            lambda: "SOME_FUTURE_SECRET" in build_child_environment(PARENT, POLICY),
            evidence=lambda: "absent anyway",
            note="The property an allowlist has and a denylist cannot: it covers the "
                 "variables that did not exist when the policy was written.")
    t.allow("a real child process, asked which seeded variables it can see",
            {"launched": "<python> -c '<dump env>'",
             "looking for": "AWS_SECRET_ACCESS_KEY, GITHUB_TOKEN, OPERATOR_SSH_KEY, "
                            "SOME_FUTURE_SECRET, MODEL_ENDPOINT"},
            lambda: {
                name: name in run(sys.executable, ["-c", DUMP], PARENT, POLICY).stdout
                for name in ("AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN",
                             "OPERATOR_SSH_KEY", "SOME_FUTURE_SECRET", "MODEL_ENDPOINT")
            },
            evidence=lambda: "every seeded secret absent; the passthrough present",
            note="Reported per variable rather than as the child's whole key list, "
                 "because the interpreter adds variables of its own at startup — "
                 "CPython sets LC_CTYPE on POSIX under locale coercion. The claim is "
                 "about what the policy passes through from the parent, not about the "
                 "child's environment being exactly one set.")
    t.allow("declining the platform essentials too",
            {"include_platform_essentials": False},
            lambda: sorted(build_child_environment(
                PARENT, EnvironmentPolicy.of({"MODEL_ENDPOINT"},
                                             include_platform_essentials=False))),
            evidence=lambda: "the default is written down and can be declined")
    t.deny("an injected value colliding with a passthrough",
           {"passthrough": "MODEL_ENDPOINT", "injected": "MODEL_ENDPOINT=https://other.test"},
           lambda: build_child_environment(
               PARENT, EnvironmentPolicy.of({"MODEL_ENDPOINT"},
                                            injected={"MODEL_ENDPOINT": "https://other.test"})),
           note="Silently choosing one would make the child's environment depend on "
                "evaluation order.")
    return t


if __name__ == "__main__":
    main(build, __file__)

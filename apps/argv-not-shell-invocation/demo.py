"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from invocation import build_invocation, run  # noqa: E402

ECHO = "import sys, json; print(json.dumps(sys.argv[1:]))"
HOSTILE = "toy; rm -rf /tmp/nothing && echo pwned | cat > /tmp/out"


def build() -> Trace:
    t = Trace(
        app="argv-not-shell-invocation",
        claim=(
            "A child process is launched from an absolute program path and a list of "
            "argument values, so a shell metacharacter inside an argument arrives as "
            "literal text — never as a second command."
        ),
        enforcement="deterministic",
        denial_type="InvocationDenied",
        redactions={sys.executable: "<python>", sys.executable.replace("\\", "/"): "<python>"},
    )
    t.allow("ordinary arguments reach the child intact",
            {"program": sys.executable, "argv": '["-c", "<echo argv>", "plain", "two words"]'},
            lambda: run(build_invocation(sys.executable, ["-c", ECHO, "plain", "two words"])).stdout.strip(),
            evidence=lambda: "the child echoed its own argv back")
    t.allow("an argument full of shell metacharacters",
            {"argument": HOSTILE},
            lambda: run(build_invocation(sys.executable, ["-c", ECHO, HOSTILE])).stdout.strip(),
            evidence=lambda: "one argument, unsplit — nothing parsed it",
            note="The check is not 'does this look dangerous'. It is 'is this ever "
                 "interpreted', and the answer is no, by construction.")
    t.deny("a relative program name",
           {"program": "python", "argv": '["-c", "print(1)"]'},
           lambda: build_invocation("python", ["-c", "print(1)"]),
           note="A bare name resolves through PATH, so it names a different file "
                "depending on where the process was started.")
    t.deny("the whole command line as one string",
           {"program": sys.executable, "arguments": "\"-c 'print(1)' && echo pwned\""},
           lambda: build_invocation(sys.executable, "-c 'print(1)' && echo pwned"),
           note="Something has to parse that back into a process, and that something "
                "is a shell.")
    t.deny("a non-string argument",
           {"argv": '["-c", "<echo argv>", 42]'},
           lambda: build_invocation(sys.executable, ["-c", ECHO, 42]))
    return t


if __name__ == "__main__":
    main(build, __file__)

"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from composition import Policy, check  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

POLICY = Policy.of(collaborators={"SqlRepository", "HttpClient", "Mailer"},
                   composition_root={"compose", "main"})
POLICY_TEXT = ("collaborators: SqlRepository, HttpClient, Mailer | "
               "composition root: compose, main")

INJECTED = ("class Service:\n"
            "    def __init__(self, repo, mailer):\n"
            "        self.repo = repo\n"
            "        self.mailer = mailer\n"
            "\n"
            "def compose():\n"
            "    return Service(SqlRepository(), Mailer())\n")

SELF_BUILT = ("class Service:\n"
              "    def __init__(self):\n"
              "        self.repo = SqlRepository()\n")

SINGLETON = ("REPO = SqlRepository()\n"
             "\n"
             "class Service:\n"
             "    def run(self):\n"
             "        return REPO\n")

DEFAULT_ARG = "def handler(repo=SqlRepository()):\n    return repo\n"

VALUE_OBJECTS = ("class Service:\n"
                 "    def __init__(self, repo):\n"
                 "        self.repo = repo\n"
                 "        self.items = []\n"
                 "        self.total = Decimal('1.00')\n")


def build() -> Trace:
    t = Trace(
        app="composition-root-construction",
        claim=(
            "A declared collaborator type may be constructed only inside the "
            "composition root; anywhere else it must arrive as a parameter."
        ),
        enforcement="deterministic",
        denial_type="n/a — this app returns (verdict, detail)",
    )

    def step(label, source, request_extra=None, note="", evidence=None):
        verdict, detail = check(source, POLICY)
        t.verdict(label,
                  dict({"source": source.replace("\n", " / ").strip(),
                        "policy": POLICY_TEXT}, **(request_extra or {})),
                  lambda v=verdict, d=detail: (v, d),
                  lambda pair: pair[0] == "passed",
                  lambda pair: f"{pair[0]} — {pair[1]}",
                  evidence=evidence, note=note)

    step("collaborators wired in the composition root", INJECTED,
         evidence=lambda: "one place knows how the system is wired")
    step("a class building its own collaborator", SELF_BUILT,
         note="The textbook violation, and the one everybody already looks for.")
    step("a module-level singleton", SINGLETON,
         evidence=lambda: "the class itself looks injected",
         note="The sneakiest shape: the wiring has moved one line out of sight, above "
              "the class that appears to receive everything.")
    step("construction in a default argument", DEFAULT_ARG,
         note="Evaluated once at import, so it is a singleton too.")
    step("value objects that are not declared collaborators", VALUE_OBJECTS,
         evidence=lambda: "lists and Decimals are not wiring",
         note="A checker that decided for itself which calls look like collaborators "
              "would flag this and be switched off by lunchtime.")
    step("a type annotation, not a construction",
         "def handle(repo: SqlRepository):\n    return repo.load()\n",
         evidence=lambda: "a mention is not a wiring")
    return t


if __name__ == "__main__":
    main(build, __file__)

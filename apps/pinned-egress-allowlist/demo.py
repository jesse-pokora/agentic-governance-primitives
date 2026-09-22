"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from egress import PinnedEgressAllowlist  # noqa: E402


def build() -> Trace:
    allowlist = PinnedEgressAllowlist(
        ["https://api.example.test", "https://mirror.example.test:8443"]
    )
    t = Trace(
        app="pinned-egress-allowlist",
        claim=(
            "An outbound request is allowed only if its scheme, host, and port all match "
            "an allowlist entry exactly — and every hop of a redirect chain is checked, "
            "not just the first."
        ),
        enforcement="deterministic",
        denial_type="EgressDenied",
    )
    allowed = "https://api.example.test, https://mirror.example.test:8443"
    t.allow("an allowlisted host on its default port",
            {"url": "https://api.example.test/v1/toy", "allowlist": allowed},
            lambda: allowlist.check("https://api.example.test/v1/toy"),
            evidence=lambda: "scheme, host and port all matched one entry")
    t.deny("a host that merely starts with the allowlisted name",
           {"url": "https://api.example.test.evil.test/v1/toy", "allowlist": allowed},
           lambda: allowlist.check("https://api.example.test.evil.test/v1/toy"),
           note="Matching is on the whole hostname, never a prefix or suffix test.")
    t.deny("the allowlisted name used as userinfo before an @",
           {"url": "https://api.example.test@evil.test/v1/toy", "real host": "evil.test"},
           lambda: allowlist.check("https://api.example.test@evil.test/v1/toy"),
           note="The name a reader's eye lands on first is not the host.")
    t.deny("an unlisted port on an allowlisted host",
           {"url": "https://api.example.test:8443/v1/toy", "allowlist": allowed},
           lambda: allowlist.check("https://api.example.test:8443/v1/toy"))
    t.allow("a redirect chain where every hop is allowlisted",
            {"hop 0": "https://api.example.test/v1/toy",
             "hop 1": "https://mirror.example.test:8443/v1/toy"},
            lambda: allowlist.check_chain(
                ["https://api.example.test/v1/toy",
                 "https://mirror.example.test:8443/v1/toy"]))
    t.deny("a 302 from an allowlisted host into an unlisted one",
           {"hop 0": "https://api.example.test/v1/toy (allowed)",
            "hop 1": "https://exfil.evil.test/collect"},
           lambda: allowlist.check_chain(
               ["https://api.example.test/v1/toy", "https://exfil.evil.test/collect"]),
           note="Checking only the first hop makes the allowlist a suggestion.")
    return t


if __name__ == "__main__":
    main(build, __file__)

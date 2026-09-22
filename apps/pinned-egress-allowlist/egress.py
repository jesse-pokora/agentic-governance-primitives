"""Pinned egress allowlist.

An outbound request is allowed only if its scheme, host, and port all match an
allowlist entry exactly. Every hop of a redirect chain is checked, not just the
first, because a 302 to an unlisted host is still egress to an unlisted host.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

DEFAULT_PORTS = {"http": 80, "https": 443}


class EgressDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class EgressRule:
    scheme: str
    host: str
    port: int

    @classmethod
    def parse(cls, spec: str) -> EgressRule:
        """Build a rule from "https://api.example.com" or "...:8443"."""
        parts = urlsplit(spec)
        scheme = parts.scheme.lower()
        host = normalize_host(parts.hostname or "")
        if not scheme or not host:
            raise ValueError(f"malformed allowlist entry: {spec!r}")
        port = parts.port or DEFAULT_PORTS.get(scheme)
        if port is None:
            raise ValueError(f"allowlist entry needs an explicit port: {spec!r}")
        return cls(scheme=scheme, host=host, port=port)


def normalize_host(host: str) -> str:
    """Lowercase, and drop one trailing root dot.

    DNS is case-insensitive and "example.com." names the same host as
    "example.com", so an exact-match allowlist that skipped this would be
    bypassed by typing the name differently.
    """
    host = host.lower()
    if host.endswith(".") and len(host) > 1:
        host = host[:-1]
    return host


@dataclass(frozen=True)
class EgressTarget:
    scheme: str
    host: str
    port: int


class PinnedEgressAllowlist:
    def __init__(self, specs: list[str]):
        self._rules = frozenset(EgressRule.parse(spec) for spec in specs)
        self._schemes = frozenset(rule.scheme for rule in self._rules)
        self._hosts = frozenset(rule.host for rule in self._rules)

    def check(self, url: str) -> EgressTarget:
        """Return the parsed target, or raise EgressDenied.

        Checks run in a fixed order — malformed, scheme, host, userinfo, port —
        so the same URL always produces the same denial reason.
        """
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        if not scheme:
            raise EgressDenied("malformed_url", url)

        # Scheme is checked before the host, so a hostless URL such as
        # "file:///etc/passwd" is denied for the reason that actually
        # disqualifies it rather than as a parse failure.
        if scheme not in self._schemes:
            raise EgressDenied("scheme_not_allowed", scheme)

        if not parts.hostname:
            raise EgressDenied("malformed_url", url)

        # Credentials in a URL both leak and confuse: in
        # "https://api.example.com@evil.test/" the host is evil.test, not the
        # name a reader's eye lands on first.
        if parts.username is not None or parts.password is not None:
            raise EgressDenied("userinfo_not_allowed", url)

        try:
            explicit_port = parts.port
        except ValueError:
            raise EgressDenied("malformed_url", url) from None

        host = normalize_host(parts.hostname)
        if host not in self._hosts:
            raise EgressDenied("host_not_allowed", host)

        port = explicit_port or DEFAULT_PORTS.get(scheme)
        if port is None:
            raise EgressDenied("malformed_url", url)

        target = EgressTarget(scheme=scheme, host=host, port=port)
        if EgressRule(scheme=scheme, host=host, port=port) not in self._rules:
            raise EgressDenied("port_not_allowed", f"{host}:{port}")

        return target

    def check_chain(self, urls: list[str]) -> EgressTarget:
        """Check every hop of a redirect chain; return the final target.

        The reason is the failing hop's own reason, and the detail names which
        hop it was, so "the redirect went somewhere unlisted" is as legible as
        a first-hop denial.
        """
        if not urls:
            raise EgressDenied("malformed_url", "empty redirect chain")

        target = None
        for index, url in enumerate(urls):
            try:
                target = self.check(url)
            except EgressDenied as denial:
                raise EgressDenied(
                    denial.reason, f"hop={index} url={url} ({denial.detail})"
                ) from None
        assert target is not None
        return target

"""Delegation scope attenuation.

Authority can only shrink as it is passed along. Each link in a delegation
chain may hold a subset of what the link before it held, never a capability the
delegator did not have, and the effective authority at the end is what survived
every link.

This is the rule that makes delegation safe to allow at all. Without it, an
agent handing work to a sub-agent is a laundering step: the sub-agent asks for
more than its delegator could have asked for, and nothing on the receiving end
can tell the difference.
"""

from __future__ import annotations

from dataclasses import dataclass


class DelegationDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Grant:
    actor: str
    capabilities: frozenset[str]

    @classmethod
    def of(cls, actor: str, capabilities: set[str]) -> Grant:
        return cls(actor=actor, capabilities=frozenset(capabilities))


def effective_authority(chain: list[Grant]) -> frozenset[str]:
    """Walk the chain and return what authority survives it.

    Raises on the first link that claims a capability its delegator did not
    hold, naming the capability rather than just the link — the added
    capability is the thing a reader needs to see.
    """
    if not chain:
        raise DelegationDenied("empty_chain", "no root grant")

    seen = {chain[0].actor}
    held = chain[0].capabilities

    for depth, link in enumerate(chain[1:], start=1):
        if link.actor in seen:
            # A loop lets authority be re-derived from a later link, which is
            # amplification wearing a longer path.
            raise DelegationDenied("delegation_loop", f"{link.actor} appears twice")
        seen.add(link.actor)

        amplified = link.capabilities - held
        if amplified:
            raise DelegationDenied(
                "amplified_capability",
                f"{link.actor} claims {', '.join(sorted(amplified))} at depth {depth}",
            )

        held = link.capabilities

    return held


def may(chain: list[Grant], capability: str) -> bool:
    """True only if the capability survived every link of the chain."""
    return capability in effective_authority(chain)

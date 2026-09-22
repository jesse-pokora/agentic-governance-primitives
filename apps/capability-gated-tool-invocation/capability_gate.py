"""Capability-gated tool invocation.

The enforcement half of a persona/capability catalog: a tool call runs only if
the calling persona's declared capability set contains that tool's exact
required capability. Denial happens before the tool function is entered, and
the catalog captured at construction is the only source of authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class CapabilityDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class ToolSpec:
    name: str
    required_capability: str
    fn: Callable[..., Any]


class CapabilityGate:
    """Mediates every tool call against a frozen persona -> capabilities map.

    The catalog is copied into immutable structures at construction: a caller
    that later mutates the dict it passed in cannot grant itself anything.
    """

    def __init__(
        self,
        personas: dict[str, set[str]],
        tools: dict[str, ToolSpec],
    ):
        self._personas = {
            name: frozenset(capabilities) for name, capabilities in personas.items()
        }
        self._tools = dict(tools)

    def capabilities_of(self, persona: str) -> frozenset[str]:
        granted = self._personas.get(persona)
        if granted is None:
            raise CapabilityDenied("unknown_persona", persona)
        return granted

    def invoke(self, persona: str, tool_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call the named tool as `persona`, or raise before entering it.

        Checks run in a fixed order — persona, tool, capability — so the same
        call always produces the same denial reason.
        """
        granted = self.capabilities_of(persona)

        tool = self._tools.get(tool_name)
        if tool is None:
            raise CapabilityDenied("unknown_tool", tool_name)

        # Exact string membership. No prefix match, no wildcard expansion, no
        # case folding: "repo.read" does not imply "repo.read_secrets", and
        # "repo.*" grants nothing at all.
        if tool.required_capability not in granted:
            raise CapabilityDenied(
                "capability_not_granted",
                f"persona={persona} tool={tool_name} "
                f"requires={tool.required_capability}",
            )

        return tool.fn(*args, **kwargs)

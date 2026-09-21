"""Governed context provenance.

Every piece of context handed to a model carries its source and an
explicit injection_disposition ("clear" vs. "untrusted") before assembly.
Assembly itself enforces this — a piece of context with no source or no
valid disposition never reaches the assembled output.
"""

from __future__ import annotations

ALLOWED_DISPOSITIONS = frozenset({"clear", "untrusted"})


class ProvenanceMissing(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def assemble_context(items: list[dict]) -> str:
    """Assemble items into a single prompt-ready string.

    Each item must be {"source": str, "injection_disposition": "clear" |
    "untrusted", "content": str}. Every assembled block is explicitly
    tagged with its source and disposition, so the model never has to
    infer or guess what it can trust.
    """
    blocks = []
    for item in items:
        source = item.get("source")
        if not source or not isinstance(source, str):
            raise ProvenanceMissing("missing_source")

        disposition = item.get("injection_disposition")
        if disposition not in ALLOWED_DISPOSITIONS:
            raise ProvenanceMissing("missing_or_invalid_injection_disposition")

        content = item.get("content", "")
        blocks.append(f"[source={source} disposition={disposition}]\n{content}")

    return "\n\n".join(blocks)

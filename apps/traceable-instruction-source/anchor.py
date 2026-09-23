"""Traceable instruction source.

An instruction is bound to the exact text at an exact location. If the source no
longer contains that text, the instruction is stale and resolving it is refused
— never silently re-read from whatever now sits at those line numbers.

Line numbers alone are the trap. Insert a paragraph above an instruction and
every anchor below it now points at somebody else's words, while still
resolving cleanly and still looking traceable. Quoting the text and hashing it
turns that from an invisible drift into a refusal.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


class StaleInstruction(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def digest_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Anchor:
    path: str
    start_line: int  # 1-based, inclusive
    end_line: int  # 1-based, inclusive
    quoted: str
    digest: str


def anchor(sources: dict[str, list[str]], path: str, start_line: int, end_line: int) -> Anchor:
    """Bind to the text currently at those lines."""
    quoted = _slice(sources, path, start_line, end_line)
    return Anchor(path, start_line, end_line, quoted, digest_of(quoted))


def resolve(anchored: Anchor, sources: dict[str, list[str]]) -> str:
    """Return the instruction text, or refuse because the source moved."""
    current = _slice(sources, anchored.path, anchored.start_line, anchored.end_line)

    if current != anchored.quoted:
        raise StaleInstruction(
            "text_changed",
            f"{anchored.path}:{anchored.start_line}-{anchored.end_line} no longer "
            f"contains the quoted instruction",
        )
    if digest_of(current) != anchored.digest:
        # Belt and braces: the quote matched but the recorded digest did not,
        # so the anchor itself was tampered with rather than the source.
        raise StaleInstruction("digest_mismatch", anchored.digest)

    return current


def _slice(sources: dict[str, list[str]], path: str, start_line: int, end_line: int) -> str:
    if path not in sources:
        raise StaleInstruction("source_missing", path)
    if start_line < 1 or end_line < start_line:
        raise StaleInstruction("invalid_range", f"{start_line}-{end_line}")

    lines = sources[path]
    if end_line > len(lines):
        raise StaleInstruction(
            "range_out_of_bounds",
            f"{path} has {len(lines)} lines, anchor needs {end_line}",
        )
    return "\n".join(lines[start_line - 1 : end_line])

"""Managed-block confinement.

An agent writes only between its own markers. Everything outside them is
human-authored and survives byte for byte, including line endings and trailing
whitespace. Content that carries a marker of its own is refused rather than
written, because a document with two start markers has no single managed
region and any later edit would have to guess which one it owns.

The write itself goes through a temporary file and os.replace, so a reader
never observes a half-written document.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

START_MARKER = "<!-- BEGIN MANAGED BLOCK -->"
END_MARKER = "<!-- END MANAGED BLOCK -->"


class ManagedWriteDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class BlockBounds:
    start: int  # index of the start marker
    end: int  # index of the end marker


def locate_block(document: str) -> BlockBounds | None:
    """Find the one managed block, or refuse to guess.

    Absent is a legal state — the block has not been created yet. Ambiguous is
    not: two starts, two ends, or an end before a start all fail closed,
    because every answer the function could give would be a guess about which
    region the agent owns.
    """
    starts = _all_indexes(document, START_MARKER)
    ends = _all_indexes(document, END_MARKER)

    if len(starts) > 1 or len(ends) > 1:
        raise ManagedWriteDenied(
            "duplicate_markers", f"start={len(starts)} end={len(ends)}"
        )
    if not starts and not ends:
        return None
    if not starts or not ends:
        raise ManagedWriteDenied(
            "unpaired_marker", "start present" if starts else "end present"
        )
    if ends[0] < starts[0]:
        raise ManagedWriteDenied("inverted_markers", f"end={ends[0]} start={starts[0]}")

    return BlockBounds(start=starts[0], end=ends[0])


def _all_indexes(haystack: str, needle: str) -> list[int]:
    found, at = [], haystack.find(needle)
    while at != -1:
        found.append(at)
        at = haystack.find(needle, at + 1)
    return found


def render_managed(document: str, content: str) -> str:
    """Return the document with the managed block set to `content`.

    Pure: computes the new document or raises, and never touches the disk. The
    caller writes only what this returns, so a refused render cannot leave a
    partially updated file behind.
    """
    if START_MARKER in content or END_MARKER in content:
        raise ManagedWriteDenied(
            "marker_injection",
            "generated content carries a managed-block marker",
        )

    block = f"{START_MARKER}\n{content}\n{END_MARKER}"
    bounds = locate_block(document)

    if bounds is None:
        # Creating the block for the first time appends it; nothing that was
        # already in the document moves.
        separator = "" if document == "" or document.endswith("\n") else "\n"
        return f"{document}{separator}{block}\n"

    before = document[: bounds.start]
    after = document[bounds.end + len(END_MARKER) :]
    return f"{before}{block}{after}"


def atomic_write(path: str, text: str) -> None:
    """Write via a temporary file in the same directory, then os.replace.

    A reader sees either the old document or the new one. This does not make a
    multi-file operation transactional — it makes one file's replacement
    indivisible.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    temporary = os.path.join(directory, f".{os.path.basename(path)}.tmp")
    with open(temporary, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temporary, path)


def write_managed_block(path: str, content: str) -> str:
    """Render first, then write. Returns the new document text."""
    document = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", newline="") as handle:
            document = handle.read()

    updated = render_managed(document, content)
    atomic_write(path, updated)
    return updated

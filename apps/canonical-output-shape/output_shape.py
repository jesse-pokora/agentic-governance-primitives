"""Canonical output shape.

Generated output is accepted only if it matches a declared shape: canonical
headings spelled exactly, in the declared order, no wrapper fence, no section
that was left empty, and a hard length bound.

Shape is checked, never repaired. A validator that silently fixes its input
stops being able to tell you the generator is drifting, and the drift then
lives in the validator's patches instead of in a test result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CANONICAL_HEADINGS = (
    "# Repository Guide",
    "## Purpose",
    "## Architecture",
    "## Key Paths",
    "## Build and Test",
    "## Conventions and Constraints",
)
MAX_WORDS = 1500

_HEADING = re.compile(r"^#{1,6} .*$", re.MULTILINE)
# A heading needs a space after the hashes. "##Key Paths" is not a heading at
# all -- it renders as body text -- so it would slip past a canonical-heading
# check while reading to a human as a section that is present.
_MALFORMED_HEADING = re.compile(r"^#{1,6}(?![#\s]).*$", re.MULTILINE)


class OutputShapeRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class ShapeReport:
    headings: tuple[str, ...]
    word_count: int


def _sections(document: str) -> list[tuple[str, str]]:
    matches = list(_HEADING.finditer(document))
    sections = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(document)
        sections.append((m.group(0).rstrip(), document[m.end():end].strip()))
    return sections


def verify_shape(document: str, max_words: int = MAX_WORDS) -> ShapeReport:
    """Accept the document, or raise naming the first violated rule.

    Optional sections may be omitted entirely — that is what "omit empty
    sections" means. What is refused is a heading present with nothing under
    it, which reads as an answer and is not one.
    """
    if document.strip() == "":
        raise OutputShapeRejected("empty_output", "no content")

    if document.lstrip().startswith("```"):
        raise OutputShapeRejected(
            "wrapped_in_fence", "the whole document is inside a code fence"
        )

    malformed = _MALFORMED_HEADING.search(document)
    if malformed:
        raise OutputShapeRejected("malformed_heading", malformed.group(0).strip())

    sections = _sections(document)
    headings = tuple(h for h, _ in sections)

    if not headings or headings[0] != CANONICAL_HEADINGS[0]:
        raise OutputShapeRejected(
            "missing_title", f"expected {CANONICAL_HEADINGS[0]!r}, got {headings[:1]}"
        )

    for heading in headings:
        if heading not in CANONICAL_HEADINGS:
            raise OutputShapeRejected("non_canonical_heading", heading)

    positions = [CANONICAL_HEADINGS.index(h) for h in headings]
    if positions != sorted(positions):
        raise OutputShapeRejected("headings_out_of_order", " | ".join(headings))
    if len(set(positions)) != len(positions):
        raise OutputShapeRejected("duplicate_heading", " | ".join(headings))

    for heading, body in sections:
        # A fenced block inside a section is legitimate content; only the whole
        # document being fenced is a wrapper, and that was checked above.
        if body == "":
            raise OutputShapeRejected("empty_section", heading)

    words = len(document.split())
    if words > max_words:
        raise OutputShapeRejected("too_long", f"{words} > {max_words} words")

    return ShapeReport(headings=headings, word_count=words)

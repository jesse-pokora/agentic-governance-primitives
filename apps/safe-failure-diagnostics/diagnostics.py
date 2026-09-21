"""Safe failure diagnostics.

A child-process failure is classified into one of a fixed vocabulary of
categories, inspecting at most MAX_INSPECTED_BYTES of its output. Only the
category — never the raw bytes — is ever persisted.
"""

from __future__ import annotations

MAX_INSPECTED_BYTES = 8192

CATEGORY_TIMEOUT = "timeout"
CATEGORY_PERMISSION_DENIED = "permission_denied"
CATEGORY_NOT_FOUND = "not_found"
CATEGORY_CRASH = "crash"
CATEGORY_UNKNOWN = "unknown"

FAILURE_CATEGORIES = frozenset(
    {
        CATEGORY_TIMEOUT,
        CATEGORY_PERMISSION_DENIED,
        CATEGORY_NOT_FOUND,
        CATEGORY_CRASH,
        CATEGORY_UNKNOWN,
    }
)

_MARKERS = (
    (b"Permission denied", CATEGORY_PERMISSION_DENIED),
    (b"No such file or directory", CATEGORY_NOT_FOUND),
    (b"Segmentation fault", CATEGORY_CRASH),
    (b"TIMEOUT_EXCEEDED", CATEGORY_TIMEOUT),
)


def classify_failure(raw_output: bytes) -> str:
    """Classify based only on the first MAX_INSPECTED_BYTES of raw_output."""
    inspected = raw_output[:MAX_INSPECTED_BYTES]
    for marker, category in _MARKERS:
        if marker in inspected:
            return category
    return CATEGORY_UNKNOWN


def persist_failure(raw_output: bytes) -> dict:
    """Return the only record ever safe to persist for this failure.

    The caller never receives raw_output back — this is the sole
    translation point between "bytes we observed" and "what gets stored".
    """
    category = classify_failure(raw_output)
    assert category in FAILURE_CATEGORIES
    return {"category": category}

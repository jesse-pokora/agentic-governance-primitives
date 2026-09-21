"""Deterministic primitives kit.

The same input byte-for-byte always produces the same canonical JSON, the
same hash, and the same safe-ID validation — across restarts, across
machines. Every function here is pure: no clock, no randomness, no locale
or environment dependence.
"""

from __future__ import annotations

import hashlib
import json
import re

_SAFE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def canonical_json(obj) -> str:
    """A single, fixed serialization for any given JSON-compatible value:
    sorted keys, no extra whitespace, ASCII-escaped, so the same value
    always serializes to the same bytes regardless of construction order.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def content_hash(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode("ascii")).hexdigest()


def is_safe_id(value: str) -> bool:
    """A fixed, locale-independent definition of a "safe" identifier:
    lowercase alphanumerics, `_`, `-`, 1-64 characters, not starting with
    `_` or `-`.
    """
    return bool(_SAFE_ID_PATTERN.match(value))

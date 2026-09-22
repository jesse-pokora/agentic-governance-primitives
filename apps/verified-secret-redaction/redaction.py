"""Verified secret redaction.

No registered secret can appear in an emitted artifact. The emitter redacts by
exact value across nested structures, then re-reads its own serialized output
and refuses to emit at all if any secret survived — it does not trust its own
redactor.

Redaction covers the *success* path: normal outputs, logs, and artifacts, not
just failure records.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

# A secret shorter than this cannot be redacted without shredding the
# surrounding document — "a" would match inside almost every word. Registering
# one is rejected rather than silently accepted, because a redactor that
# destroys its input is not a redactor.
MIN_SECRET_LENGTH = 4


class RedactionFailure(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


class SecretRegistry:
    """Holds the secret values that must never reach an artifact.

    `correlation_key` is required, not defaulted: placeholders are HMACs, so
    the same secret produces the same placeholder everywhere the key is the
    same — which is what makes redacted logs still correlatable — while a
    placeholder on its own reveals nothing without the key.
    """

    def __init__(self, secrets: list[str], correlation_key: bytes):
        if not correlation_key:
            raise RedactionFailure("invalid_correlation_key", "key must be non-empty")
        for secret in secrets:
            if len(secret) < MIN_SECRET_LENGTH:
                raise RedactionFailure(
                    "invalid_secret", f"shorter than {MIN_SECRET_LENGTH} characters"
                )
        self._key = correlation_key
        # Longest first: if one secret contains another, replacing the shorter
        # one first would leave a mangled fragment of the longer one behind.
        self._secrets = tuple(sorted(set(secrets), key=len, reverse=True))

    @property
    def secrets(self) -> tuple[str, ...]:
        return self._secrets

    def placeholder(self, secret: str) -> str:
        digest = hmac.new(self._key, secret.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"[redacted:{digest[:12]}]"

    def _redact_text(self, text: str) -> str:
        for secret in self._secrets:
            if secret in text:
                text = text.replace(secret, self.placeholder(secret))
        return text

    def redact(self, obj: Any) -> Any:
        """Walk a structure, replacing every secret occurrence by value.

        Dict *keys* are redacted too — a secret used as a key is just as
        exposed as one used as a value.
        """
        if isinstance(obj, str):
            return self._redact_text(obj)
        if isinstance(obj, bytes):
            return self._redact_text(obj.decode("utf-8", errors="replace")).encode(
                "utf-8"
            )
        if isinstance(obj, dict):
            return {self.redact(key): self.redact(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [self.redact(item) for item in obj]
        if isinstance(obj, tuple):
            return tuple(self.redact(item) for item in obj)
        return obj

    def assert_clean(self, serialized: str) -> None:
        """Raise if any secret survives in already-serialized output.

        The exception names only the placeholder — an error message that
        quoted the leaked secret would be one more place the secret appears.
        """
        for secret in self._secrets:
            if secret in serialized:
                raise RedactionFailure(
                    "secret_survived_redaction", self.placeholder(secret)
                )

    def emit(self, obj: Any) -> str:
        """Redact, serialize, verify, and only then hand the artifact back."""
        serialized = json.dumps(
            self.redact(obj), sort_keys=True, separators=(",", ":"), default=repr
        )
        self.assert_clean(serialized)
        return serialized

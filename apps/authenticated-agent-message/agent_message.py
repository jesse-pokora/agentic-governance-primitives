"""Authenticated agent message.

A message between agents is accepted only if it is signed by a sender the
recipient knows, addressed to that recipient, and carries a sequence number
strictly greater than the last one accepted from that sender.

This is an envelope, not a bus. It has no router, no queue, no delivery and no
loop — it answers one question a recipient must answer about one message it has
already received by some means: is this from who it says, for me, and new.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any


class MessageRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class Message:
    sender: str
    recipient: str
    sequence: int
    payload: dict
    signature: str = ""

    def signing_input(self) -> bytes:
        # Every field the recipient will act on is covered. A signature over
        # the payload alone would let an intercepted message be re-addressed
        # to a different agent and still verify.
        return canonical_json(
            {
                "sender": self.sender,
                "recipient": self.recipient,
                "sequence": self.sequence,
                "payload": self.payload,
            }
        ).encode("utf-8")


def sign(message: Message, key: bytes) -> Message:
    signature = hmac.new(key, message.signing_input(), hashlib.sha256).hexdigest()
    return Message(
        sender=message.sender,
        recipient=message.recipient,
        sequence=message.sequence,
        payload=message.payload,
        signature=signature,
    )


@dataclass
class Recipient:
    """One agent's view: who it is, whose keys it holds, what it has accepted."""

    identity: str
    keys: dict[str, bytes]
    last_sequence: dict[str, int] = field(default_factory=dict)

    def accept(self, message: Message) -> dict:
        """Return the payload, or refuse.

        Checks run in a fixed order — sender, signature, addressee, sequence —
        so the same message always produces the same rejection.
        """
        key = self.keys.get(message.sender)
        if key is None:
            raise MessageRejected("unknown_sender", message.sender)

        expected = hmac.new(key, message.signing_input(), hashlib.sha256).hexdigest()
        if not message.signature or not hmac.compare_digest(expected, message.signature):
            raise MessageRejected("signature_invalid", message.sender)

        if message.recipient != self.identity:
            # Signed, genuine, and not for me. Acting on it is the agentic
            # equivalent of opening someone else's post.
            raise MessageRejected(
                "misaddressed", f"addressed to {message.recipient}, I am {self.identity}"
            )

        last = self.last_sequence.get(message.sender)
        if last is not None and message.sequence <= last:
            raise MessageRejected(
                "replayed", f"sequence {message.sequence} <= last accepted {last}"
            )

        # A gap is allowed: the missing message may have been dropped, and
        # refusing to move on would let one lost message wedge the channel.
        # What must never be accepted is a sequence already seen or older.
        self.last_sequence[message.sender] = message.sequence
        return message.payload

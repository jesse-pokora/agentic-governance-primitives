"""Deterministic ledger replay.

Replaying a ledger from genesis reproduces the final state byte-for-byte, and
any state a replay cannot reproduce is rejected. Where an authenticated
transition ledger proves the *log* is intact, this proves the *state* is
derivable from that log — so state can never quietly drift away from its
evidence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def digest_of(state: dict) -> str:
    return hashlib.sha256(canonical_json(state).encode("utf-8")).hexdigest()


GENESIS_STATE: dict = {"open_findings": [], "reviewer": None}
GENESIS_DIGEST = digest_of(GENESIS_STATE)


class ReplayRejected(Exception):
    def __init__(self, reason: str, detail: str = "", index: int | None = None):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail
        self.index = index


@dataclass(frozen=True)
class Event:
    type: str
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Entry:
    index: int
    event: Event
    state_digest_after: str


# --- Reducers: pure state -> state, never mutating their input --------------


def _open_finding(state: dict, payload: dict) -> dict:
    finding_id = payload["id"]
    if finding_id in state["open_findings"]:
        raise ReplayRejected("inapplicable_event", f"already open: {finding_id}")
    return {**state, "open_findings": sorted(state["open_findings"] + [finding_id])}


def _resolve_finding(state: dict, payload: dict) -> dict:
    finding_id = payload["id"]
    if finding_id not in state["open_findings"]:
        raise ReplayRejected("inapplicable_event", f"not open: {finding_id}")
    remaining = [f for f in state["open_findings"] if f != finding_id]
    return {**state, "open_findings": sorted(remaining)}


def _assign_reviewer(state: dict, payload: dict) -> dict:
    return {**state, "reviewer": payload["persona"]}


REDUCERS: dict[str, Callable[[dict, dict], dict]] = {
    "open_finding": _open_finding,
    "resolve_finding": _resolve_finding,
    "assign_reviewer": _assign_reviewer,
}


def apply_event(state: dict, event: Event) -> dict:
    reducer = REDUCERS.get(event.type)
    if reducer is None:
        # Skipping an unrecognized event would silently fork state away from
        # the log that is supposed to explain it.
        raise ReplayRejected("unknown_event_type", event.type)
    return reducer(state, event.payload)


@dataclass
class ReplayResult:
    state: dict
    digest: str
    checkpoints: list[str]


def replay(events: list[Event]) -> ReplayResult:
    """Fold events over the genesis state, recording a digest after each."""
    state = dict(GENESIS_STATE)
    checkpoints: list[str] = []
    for index, event in enumerate(events):
        try:
            state = apply_event(state, event)
        except ReplayRejected as rejection:
            raise ReplayRejected(rejection.reason, rejection.detail, index) from None
        checkpoints.append(digest_of(state))
    return ReplayResult(state=state, digest=digest_of(state), checkpoints=checkpoints)


class ReplayableLedger:
    def __init__(self):
        self._entries: list[Entry] = []
        self.state: dict = dict(GENESIS_STATE)

    @property
    def entries(self) -> list[Entry]:
        return self._entries

    def append(self, event: Event) -> int:
        self.state = apply_event(self.state, event)
        index = len(self._entries)
        self._entries.append(
            Entry(index=index, event=event, state_digest_after=digest_of(self.state))
        )
        return index

    def verify(self) -> ReplayResult:
        """Replay from genesis and reject any state the replay can't reproduce.

        Two distinct failures: a recorded checkpoint that replay disagrees with
        (pinpointed to the first divergent index), and a current state that is
        not the replay's final state — the signature of a write that bypassed
        the log entirely.
        """
        result = replay([entry.event for entry in self._entries])

        for entry, recomputed in zip(self._entries, result.checkpoints):
            if entry.state_digest_after != recomputed:
                raise ReplayRejected(
                    "checkpoint_divergence",
                    f"recorded={entry.state_digest_after} replayed={recomputed}",
                    entry.index,
                )

        if digest_of(self.state) != result.digest:
            raise ReplayRejected(
                "state_not_derivable",
                f"current={digest_of(self.state)} replayed={result.digest}",
            )

        return result

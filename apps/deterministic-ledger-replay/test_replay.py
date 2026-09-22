import unittest
from dataclasses import replace

from replay import (
    GENESIS_DIGEST,
    Event,
    digest_of,
    ReplayableLedger,
    ReplayRejected,
    replay,
)

EVENTS = [
    Event("assign_reviewer", {"persona": "toy-reviewer"}),
    Event("open_finding", {"id": "F-002"}),
    Event("open_finding", {"id": "F-001"}),
    Event("resolve_finding", {"id": "F-002"}),
]


def build_ledger(events=EVENTS):
    ledger = ReplayableLedger()
    for event in events:
        ledger.append(event)
    return ledger


class DeterministicLedgerReplayTests(unittest.TestCase):
    def test_replaying_the_same_events_twice_gives_the_same_digest(self):
        self.assertEqual(replay(EVENTS).digest, replay(list(EVENTS)).digest)

    def test_replay_reproduces_the_live_state_byte_for_byte(self):
        ledger = build_ledger()
        result = ledger.verify()

        self.assertEqual(result.state, ledger.state)
        self.assertEqual(result.state, {"open_findings": ["F-001"], "reviewer": "toy-reviewer"})

    def test_the_same_events_in_a_different_order_are_a_different_state(self):
        # Identical multiset of events, opposite order. A state derived from an
        # unordered set of events would call these two histories equal.
        first = Event("assign_reviewer", {"persona": "toy-reviewer-a"})
        second = Event("assign_reviewer", {"persona": "toy-reviewer-b"})

        forward = replay([first, second])
        backward = replay([second, first])

        self.assertEqual(forward.state["reviewer"], "toy-reviewer-b")
        self.assertEqual(backward.state["reviewer"], "toy-reviewer-a")
        self.assertNotEqual(forward.digest, backward.digest)

    def test_state_key_order_does_not_change_the_digest(self):
        # Canonical JSON, so a dict built in a different insertion order — or on
        # a different interpreter — hashes the same.
        self.assertEqual(
            digest_of({"open_findings": ["F-001"], "reviewer": "toy-reviewer"}),
            digest_of({"reviewer": "toy-reviewer", "open_findings": ["F-001"]}),
        )

    def test_an_empty_ledger_replays_to_the_genesis_digest(self):
        self.assertEqual(replay([]).digest, GENESIS_DIGEST)
        self.assertEqual(ReplayableLedger().verify().digest, GENESIS_DIGEST)

    def test_a_write_that_bypassed_the_log_is_rejected(self):
        ledger = build_ledger()
        # Out-of-band mutation: state changed without an event explaining it.
        ledger.state["open_findings"] = ledger.state["open_findings"] + ["F-999"]

        with self.assertRaises(ReplayRejected) as ctx:
            ledger.verify()

        self.assertEqual(ctx.exception.reason, "state_not_derivable")

    def test_a_tampered_checkpoint_is_pinpointed_to_its_first_divergent_index(self):
        ledger = build_ledger()
        ledger.entries[1] = replace(ledger.entries[1], state_digest_after="f" * 64)

        with self.assertRaises(ReplayRejected) as ctx:
            ledger.verify()

        self.assertEqual(ctx.exception.reason, "checkpoint_divergence")
        self.assertEqual(ctx.exception.index, 1)

    def test_an_unknown_event_type_fails_closed_rather_than_being_skipped(self):
        with self.assertRaises(ReplayRejected) as ctx:
            replay([Event("assign_reviewer", {"persona": "toy-reviewer"}),
                    Event("quietly_close_everything", {})])

        self.assertEqual(ctx.exception.reason, "unknown_event_type")
        self.assertEqual(ctx.exception.index, 1)

    def test_an_inapplicable_event_fails_closed(self):
        with self.assertRaises(ReplayRejected) as ctx:
            replay([Event("resolve_finding", {"id": "F-never-opened"})])

        self.assertEqual(ctx.exception.reason, "inapplicable_event")
        self.assertEqual(ctx.exception.index, 0)


if __name__ == "__main__":
    unittest.main()

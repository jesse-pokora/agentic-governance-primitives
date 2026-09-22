import unittest

from agent_message import Message, MessageRejected, Recipient, sign

PLANNER_KEY = b"toy-planner-key"
WORKER_KEY = b"toy-worker-key"


def planner_message(recipient="worker-agent", sequence=1, payload=None):
    return sign(
        Message("planner-agent", recipient, sequence,
                payload if payload is not None else {"task": "summarize svc-fake-a"}),
        PLANNER_KEY,
    )


class AuthenticatedAgentMessageTests(unittest.TestCase):
    def setUp(self):
        self.worker = Recipient(
            identity="worker-agent",
            keys={"planner-agent": PLANNER_KEY, "auditor-agent": WORKER_KEY},
        )

    def test_a_signed_addressed_new_message_is_accepted(self):
        payload = self.worker.accept(planner_message())
        self.assertEqual(payload["task"], "summarize svc-fake-a")

    def test_an_unsigned_message_is_rejected(self):
        unsigned = Message("planner-agent", "worker-agent", 1, {"task": "toy"})

        with self.assertRaises(MessageRejected) as ctx:
            self.worker.accept(unsigned)

        self.assertEqual(ctx.exception.reason, "signature_invalid")

    def test_a_message_signed_with_the_wrong_key_is_rejected(self):
        forged = sign(Message("planner-agent", "worker-agent", 1, {"task": "toy"}),
                      b"attacker-key")

        with self.assertRaises(MessageRejected) as ctx:
            self.worker.accept(forged)

        self.assertEqual(ctx.exception.reason, "signature_invalid")

    def test_a_payload_edited_after_signing_is_rejected(self):
        original = planner_message()
        tampered = Message(original.sender, original.recipient, original.sequence,
                           {"task": "delete svc-fake-a"}, original.signature)

        with self.assertRaises(MessageRejected) as ctx:
            self.worker.accept(tampered)

        self.assertEqual(ctx.exception.reason, "signature_invalid")

    def test_a_genuine_message_for_someone_else_is_rejected(self):
        # Correctly signed by a known sender, just not addressed here. The
        # signature covers the recipient, so it cannot be re-addressed either.
        for_auditor = planner_message(recipient="auditor-agent")

        with self.assertRaises(MessageRejected) as ctx:
            self.worker.accept(for_auditor)

        self.assertEqual(ctx.exception.reason, "misaddressed")

    def test_re_addressing_an_intercepted_message_invalidates_it(self):
        intercepted = planner_message(recipient="auditor-agent")
        redirected = Message(intercepted.sender, "worker-agent", intercepted.sequence,
                             intercepted.payload, intercepted.signature)

        with self.assertRaises(MessageRejected) as ctx:
            self.worker.accept(redirected)

        self.assertEqual(ctx.exception.reason, "signature_invalid")

    def test_replaying_an_accepted_message_is_rejected(self):
        message = planner_message(sequence=5)
        self.worker.accept(message)

        with self.assertRaises(MessageRejected) as ctx:
            self.worker.accept(message)

        self.assertEqual(ctx.exception.reason, "replayed")

    def test_an_older_sequence_is_rejected(self):
        self.worker.accept(planner_message(sequence=5))

        with self.assertRaises(MessageRejected) as ctx:
            self.worker.accept(planner_message(sequence=4))

        self.assertEqual(ctx.exception.reason, "replayed")

    def test_a_gap_in_the_sequence_is_accepted(self):
        # A dropped message must not wedge the channel forever.
        self.worker.accept(planner_message(sequence=1))
        self.worker.accept(planner_message(sequence=9))

        self.assertEqual(self.worker.last_sequence["planner-agent"], 9)

    def test_an_unknown_sender_is_rejected(self):
        stranger = sign(Message("rogue-agent", "worker-agent", 1, {"task": "toy"}),
                        b"rogue-key")

        with self.assertRaises(MessageRejected) as ctx:
            self.worker.accept(stranger)

        self.assertEqual(ctx.exception.reason, "unknown_sender")

    def test_each_sender_has_its_own_sequence(self):
        self.worker.accept(planner_message(sequence=7))
        auditor = sign(Message("auditor-agent", "worker-agent", 1, {"task": "audit"}),
                       WORKER_KEY)

        self.assertEqual(self.worker.accept(auditor)["task"], "audit")


if __name__ == "__main__":
    unittest.main()

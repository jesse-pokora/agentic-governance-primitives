import unittest

from reuse import REUSE_REASONS, Artifact, digest_of, obtain

INPUTS = {"repo": "toy-repo", "files": ["a.py", "b.py"]}
CHANGED = {"repo": "toy-repo", "files": ["a.py", "b.py", "c.py"]}
VERSION = "summarizer-2.1.0"


class ProducerSpy:
    def __init__(self, result="freshly generated guide"):
        self.calls = 0
        self.result = result

    def __call__(self):
        self.calls += 1
        return self.result


def valid_artifact(inputs=INPUTS, version=VERSION, generation=1):
    return Artifact(content="existing guide", input_digest=digest_of(inputs),
                    producer_version=version, generation=generation)


class ValidatedArtifactReuseTests(unittest.TestCase):
    def setUp(self):
        self.produce = ProducerSpy()

    def test_a_valid_artifact_is_reused_without_regenerating(self):
        decision = obtain(valid_artifact(), INPUTS, VERSION, self.produce)

        self.assertTrue(decision.reused)
        self.assertEqual(decision.reason, "valid_for_these_inputs")
        self.assertEqual(decision.artifact.content, "existing guide")
        self.assertEqual(self.produce.calls, 0)

    def test_changed_inputs_regenerate(self):
        decision = obtain(valid_artifact(), CHANGED, VERSION, self.produce)

        self.assertFalse(decision.reused)
        self.assertEqual(decision.reason, "inputs_changed")
        self.assertEqual(self.produce.calls, 1)

    def test_a_changed_producer_version_regenerates(self):
        decision = obtain(valid_artifact(), INPUTS, "summarizer-3.0.0", self.produce)

        self.assertFalse(decision.reused)
        self.assertEqual(decision.reason, "producer_version_changed")
        self.assertEqual(self.produce.calls, 1)

    def test_no_existing_artifact_regenerates(self):
        decision = obtain(None, INPUTS, VERSION, self.produce)

        self.assertFalse(decision.reused)
        self.assertEqual(decision.reason, "no_existing_artifact")
        self.assertEqual(decision.artifact.generation, 1)

    def test_an_artifact_with_a_malformed_digest_regenerates(self):
        for bad in ("", "not-a-digest", "a" * 63, "z" * 64):
            with self.subTest(digest=bad):
                spy = ProducerSpy()
                decision = obtain(
                    Artifact("stale", bad, VERSION, 1), INPUTS, VERSION, spy
                )
                self.assertEqual(decision.reason, "artifact_corrupt")
                self.assertEqual(spy.calls, 1)

    def test_input_key_order_does_not_force_a_regeneration(self):
        reordered = {"files": ["a.py", "b.py"], "repo": "toy-repo"}

        decision = obtain(valid_artifact(), reordered, VERSION, self.produce)

        self.assertTrue(decision.reused)
        self.assertEqual(self.produce.calls, 0)

    def test_input_order_within_a_list_does_change_the_answer(self):
        # A list is ordered data, not a set. Treating ["a","b"] and ["b","a"]
        # as the same input would be a guess about what the list means.
        decision = obtain(valid_artifact(), {"repo": "toy-repo", "files": ["b.py", "a.py"]},
                          VERSION, self.produce)

        self.assertFalse(decision.reused)
        self.assertEqual(decision.reason, "inputs_changed")

    def test_regeneration_advances_the_generation_counter(self):
        decision = obtain(valid_artifact(generation=4), CHANGED, VERSION, self.produce)

        self.assertEqual(decision.artifact.generation, 5)

    def test_reuse_does_not_advance_the_generation_counter(self):
        decision = obtain(valid_artifact(generation=4), INPUTS, VERSION, self.produce)

        self.assertEqual(decision.artifact.generation, 4)

    def test_every_decision_carries_a_reason_from_the_fixed_vocabulary(self):
        decisions = [
            obtain(valid_artifact(), INPUTS, VERSION, ProducerSpy()),
            obtain(valid_artifact(), CHANGED, VERSION, ProducerSpy()),
            obtain(None, INPUTS, VERSION, ProducerSpy()),
            obtain(valid_artifact(), INPUTS, "other", ProducerSpy()),
            obtain(Artifact("x", "bad", VERSION, 1), INPUTS, VERSION, ProducerSpy()),
        ]

        self.assertTrue({d.reason for d in decisions} <= REUSE_REASONS)
        self.assertEqual(len({d.reason for d in decisions}), 5)


if __name__ == "__main__":
    unittest.main()

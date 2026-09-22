import unittest

from instruction_set import (
    InstructionDrift,
    InstructionManifest,
    PinnedInstructionSet,
    run_under,
    verify,
)

AGENTS_MD = b"# toy agent instructions\nalways state the atomic claim\n"
REVIEW_MD = b"# toy review instructions\nreject findings without evidence\n"


class HashPinnedInstructionSetTests(unittest.TestCase):
    def setUp(self):
        self.files = {"AGENTS.md": AGENTS_MD, "REVIEW.md": REVIEW_MD}
        self.pinned = PinnedInstructionSet.pin(InstructionManifest.from_files(self.files))
        self.ran = 0

    def _action(self):
        self.ran += 1
        return "executed"

    def test_identical_instruction_set_runs_the_action(self):
        current = InstructionManifest.from_files(dict(self.files))
        self.assertEqual(run_under(self.pinned, current, self._action), "executed")
        self.assertEqual(self.ran, 1)

    def test_one_edited_byte_is_drift_and_the_action_never_runs(self):
        drifted = dict(self.files)
        drifted["AGENTS.md"] = AGENTS_MD.replace(b"always", b"rarely")

        with self.assertRaises(InstructionDrift) as ctx:
            run_under(self.pinned, InstructionManifest.from_files(drifted), self._action)

        self.assertEqual(ctx.exception.reason, "content_drift")
        self.assertIn("AGENTS.md", ctx.exception.detail)
        self.assertEqual(self.ran, 0)

    def test_an_added_instruction_file_is_drift(self):
        extra = dict(self.files)
        extra["SHADOW.md"] = b"# toy file the pinned run never saw\n"

        with self.assertRaises(InstructionDrift) as ctx:
            verify(self.pinned, InstructionManifest.from_files(extra))

        self.assertEqual(ctx.exception.reason, "instruction_added")
        self.assertEqual(ctx.exception.detail, "SHADOW.md")

    def test_a_removed_instruction_file_is_drift(self):
        fewer = {"AGENTS.md": AGENTS_MD}

        with self.assertRaises(InstructionDrift) as ctx:
            verify(self.pinned, InstructionManifest.from_files(fewer))

        self.assertEqual(ctx.exception.reason, "instruction_removed")
        self.assertEqual(ctx.exception.detail, "REVIEW.md")

    def test_swapping_contents_between_two_files_is_still_drift(self):
        # The multiset of file hashes is unchanged — only which name carries
        # which hash. A manifest that hashed contents without binding them to
        # names would call this identical.
        swapped = {"AGENTS.md": REVIEW_MD, "REVIEW.md": AGENTS_MD}

        with self.assertRaises(InstructionDrift) as ctx:
            verify(self.pinned, InstructionManifest.from_files(swapped))

        self.assertEqual(ctx.exception.reason, "content_drift")

    def test_manifest_digest_is_independent_of_insertion_order(self):
        forward = InstructionManifest.from_files(
            {"AGENTS.md": AGENTS_MD, "REVIEW.md": REVIEW_MD}
        )
        backward = InstructionManifest.from_files(
            {"REVIEW.md": REVIEW_MD, "AGENTS.md": AGENTS_MD}
        )
        self.assertEqual(forward.digest, backward.digest)
        self.assertEqual(forward.digest, self.pinned.manifest_digest)


if __name__ == "__main__":
    unittest.main()

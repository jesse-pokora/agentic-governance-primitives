import os
import tempfile
import unittest

from attestation import AttestationMismatch, attest, init_snapshot_repo


class WorkspaceAttestationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo_dir = self.tmp.name

        with open(os.path.join(self.repo_dir, "existing.txt"), "w") as f:
            f.write("original content\n")
        with open(os.path.join(self.repo_dir, "to_delete.txt"), "w") as f:
            f.write("will be deleted\n")

        init_snapshot_repo(self.repo_dir)  # real 'before' git-worktree snapshot

    def tearDown(self):
        self.tmp.cleanup()

    def test_claim_that_exactly_matches_the_real_diff_passes(self):
        with open(os.path.join(self.repo_dir, "new_file.txt"), "w") as f:
            f.write("brand new toy file\n")

        result = attest(
            self.repo_dir,
            claimed_added=["new_file.txt"],
            claimed_modified=[],
            claimed_deleted=[],
        )
        self.assertEqual(result.added, frozenset({"new_file.txt"}))

    def test_modified_and_deleted_files_are_both_detected(self):
        with open(os.path.join(self.repo_dir, "existing.txt"), "w") as f:
            f.write("changed content\n")
        os.remove(os.path.join(self.repo_dir, "to_delete.txt"))

        result = attest(
            self.repo_dir,
            claimed_added=[],
            claimed_modified=["existing.txt"],
            claimed_deleted=["to_delete.txt"],
        )
        self.assertEqual(result.modified, frozenset({"existing.txt"}))
        self.assertEqual(result.deleted, frozenset({"to_delete.txt"}))

    def test_claim_missing_an_actual_change_fails_closed(self):
        with open(os.path.join(self.repo_dir, "new_file.txt"), "w") as f:
            f.write("brand new toy file\n")
        os.remove(os.path.join(self.repo_dir, "to_delete.txt"))

        with self.assertRaises(AttestationMismatch) as ctx:
            attest(
                self.repo_dir,
                claimed_added=["new_file.txt"],
                claimed_modified=[],
                claimed_deleted=[],  # omits the real deletion
            )
        self.assertIn("to_delete.txt", ctx.exception.actual["deleted"])

    def test_claim_of_a_change_that_never_happened_fails_closed(self):
        with self.assertRaises(AttestationMismatch) as ctx:
            attest(
                self.repo_dir,
                claimed_added=["phantom_file.txt"],
                claimed_modified=[],
                claimed_deleted=[],
            )
        self.assertIn("phantom_file.txt", ctx.exception.claimed["added"])
        self.assertEqual(ctx.exception.actual["added"], [])


if __name__ == "__main__":
    unittest.main()

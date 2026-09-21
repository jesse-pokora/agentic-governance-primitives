import os
import tempfile
import unittest

from launcher import (
    HashPinnedLauncher,
    IdentityMismatch,
    PinnedIdentity,
    PinnedIdentityPolicy,
    sha256_of_file,
)


class HashPinnedIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.trusted_dir = os.path.join(self.tmp.name, "trusted_bin")
        self.attacker_dir = os.path.join(self.tmp.name, "attacker_bin")
        os.makedirs(self.trusted_dir)
        os.makedirs(self.attacker_dir)

        self.trusted_path = os.path.join(self.trusted_dir, "deploy-tool")
        with open(self.trusted_path, "wb") as f:
            f.write(b"#!/bin/sh\necho toy-deploy-tool v1\n")

        self.policy = PinnedIdentityPolicy(
            {
                "deploy-tool": PinnedIdentity(
                    absolute_path=self.trusted_path,
                    sha256=sha256_of_file(self.trusted_path),
                )
            }
        )
        self.launcher = HashPinnedLauncher(self.policy)

    def tearDown(self):
        self.tmp.cleanup()

    def test_allows_exact_path_and_hash_match(self):
        content = self.launcher.launch("deploy-tool", self.trusted_path)
        self.assertIn(b"toy-deploy-tool", content)

    def test_denies_path_hijack_same_name_different_location(self):
        # An impostor with the identical name sits earlier on a fake PATH.
        impostor_path = os.path.join(self.attacker_dir, "deploy-tool")
        with open(impostor_path, "wb") as f:
            f.write(b"#!/bin/sh\necho toy-deploy-tool v1\n")  # byte-identical content

        with self.assertRaises(IdentityMismatch) as ctx:
            self.launcher.launch("deploy-tool", impostor_path)
        self.assertIn("path_mismatch", ctx.exception.reason)

    def test_denies_tampered_content_at_the_pinned_path(self):
        with open(self.trusted_path, "wb") as f:
            f.write(b"#!/bin/sh\necho backdoored\n")

        with self.assertRaises(IdentityMismatch) as ctx:
            self.launcher.launch("deploy-tool", self.trusted_path)
        self.assertIn("hash_mismatch", ctx.exception.reason)

    def test_denies_unknown_executable_name(self):
        with self.assertRaises(IdentityMismatch) as ctx:
            self.launcher.launch("unregistered-tool", self.trusted_path)
        self.assertIn("no pinned identity", ctx.exception.reason)


if __name__ == "__main__":
    unittest.main()

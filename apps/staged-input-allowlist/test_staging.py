import os
import tempfile
import unittest

from staging import EXCLUSION_REASONS, StagingPolicy, StagingRefused, stage

POLICY = StagingPolicy(
    allowed_suffixes=frozenset({".py", ".md", ".txt"}),
    denied_names=frozenset({".env", "id_rsa", "credentials.json"}),
    max_file_bytes=1024,
    max_files=10,
    max_total_bytes=8192,
)


class StagedInputAllowlistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = os.path.join(self.tmp.name, "repo")
        self.dest = os.path.join(self.tmp.name, "staging")
        os.makedirs(os.path.join(self.src, ".git"))
        os.makedirs(os.path.join(self.src, "pkg"))
        self.put("README.md", "# toy\n")
        self.put("pkg/main.py", "print('toy')\n")
        self.put(".env", "TOKEN=toy-secret-AAAA1111\n")
        self.put("id_rsa", "-----BEGIN PRIVATE KEY-----\n")
        self.put("logo.png", "\x89PNG toy\n")
        self.put(".git/config", "[core]\n")
        self.put("huge.txt", "x" * 2048)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, text):
        path = os.path.join(self.src, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_only_allowlisted_files_are_staged(self):
        result = stage(self.src, self.dest, POLICY)

        self.assertEqual(result.staged, ["README.md", "pkg/main.py"])
        self.assertTrue(os.path.isfile(os.path.join(self.dest, "pkg", "main.py")))

    def test_secret_filenames_are_excluded_by_name(self):
        excluded = dict(stage(self.src, self.dest, POLICY).excluded)

        self.assertEqual(excluded[".env"], "denied_name")
        self.assertEqual(excluded["id_rsa"], "denied_name")

    def test_an_unlisted_suffix_is_excluded(self):
        excluded = dict(stage(self.src, self.dest, POLICY).excluded)
        self.assertEqual(excluded["logo.png"], "suffix_not_allowed")

    def test_version_control_metadata_is_excluded(self):
        excluded = dict(stage(self.src, self.dest, POLICY).excluded)
        self.assertEqual(excluded[".git/config"], "vcs_metadata")

    def test_an_oversized_file_is_excluded(self):
        excluded = dict(stage(self.src, self.dest, POLICY).excluded)
        self.assertEqual(excluded["huge.txt"], "too_large")

    def test_a_symlink_is_excluded_rather_than_followed(self):
        try:
            os.symlink(os.path.join(self.src, "README.md"),
                       os.path.join(self.src, "link.md"))
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation not permitted on this platform/account")

        excluded = dict(stage(self.src, self.dest, POLICY).excluded)
        self.assertEqual(excluded["link.md"], "symlink")

    def test_nothing_is_dropped_without_a_reason(self):
        result = stage(self.src, self.dest, POLICY)
        source_files = {
            os.path.relpath(os.path.join(d, n), self.src).replace("\\", "/")
            for d, _, fs in os.walk(self.src) for n in fs
        }

        accounted = set(result.staged) | {p for p, _ in result.excluded}
        self.assertEqual(accounted, source_files)
        self.assertTrue({r for _, r in result.excluded} <= EXCLUSION_REASONS)

    def test_the_manifest_lists_exactly_the_staged_set(self):
        result = stage(self.src, self.dest, POLICY)
        excluded_paths = {p for p, _ in result.excluded}

        self.assertEqual(result.manifest, sorted(result.staged))
        self.assertFalse(set(result.manifest) & excluded_paths)

    def test_exceeding_the_file_count_cap_stages_nothing(self):
        for n in range(12):
            self.put(f"pkg/file_{n}.py", "toy\n")

        with self.assertRaises(StagingRefused) as ctx:
            stage(self.src, self.dest, POLICY)

        self.assertEqual(ctx.exception.reason, "file_count_cap")
        self.assertFalse(os.path.exists(self.dest))

    def test_exceeding_the_total_byte_cap_stages_nothing(self):
        policy = StagingPolicy(
            allowed_suffixes=POLICY.allowed_suffixes, denied_names=POLICY.denied_names,
            max_file_bytes=1024, max_files=10, max_total_bytes=16,
        )

        with self.assertRaises(StagingRefused) as ctx:
            stage(self.src, self.dest, policy)

        self.assertEqual(ctx.exception.reason, "total_byte_cap")
        self.assertFalse(os.path.exists(self.dest))


if __name__ == "__main__":
    unittest.main()

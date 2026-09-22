import os
import tempfile
import unittest

from confined_writer import ConfinedWriter, WriteDenied


def symlinks_available(tmpdir: str) -> bool:
    """Creating symlinks needs Developer Mode or admin rights on Windows."""
    probe_target = os.path.join(tmpdir, "probe_target")
    probe_link = os.path.join(tmpdir, "probe_link")
    os.makedirs(probe_target, exist_ok=True)
    try:
        os.symlink(probe_target, probe_link, target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        return False
    os.remove(probe_link)
    return True


class WriteScopeConfinementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "work")
        self.outside = os.path.join(self.tmp.name, "outside")
        # A sibling whose name has the scope root as a string prefix.
        self.prefix_sibling = os.path.join(self.tmp.name, "work-evil")
        for path in (self.root, self.outside, self.prefix_sibling):
            os.makedirs(path)

        self.writer = ConfinedWriter(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_write_inside_the_scope_lands(self):
        target = self.writer.write("notes/toy.txt", b"toy payload")
        self.assertTrue(os.path.isfile(target))
        with open(target, "rb") as f:
            self.assertEqual(f.read(), b"toy payload")

    def test_parent_traversal_is_denied_and_writes_nothing(self):
        escaped = os.path.join(self.outside, "stolen.txt")

        with self.assertRaises(WriteDenied) as ctx:
            self.writer.write(os.path.join("..", "outside", "stolen.txt"), b"nope")

        self.assertEqual(ctx.exception.reason, "traversal_escape")
        self.assertFalse(os.path.exists(escaped))

    def test_an_absolute_path_outside_the_scope_is_denied(self):
        escaped = os.path.join(self.outside, "stolen.txt")

        with self.assertRaises(WriteDenied) as ctx:
            self.writer.write(escaped, b"nope")

        self.assertEqual(ctx.exception.reason, "outside_scope")
        self.assertFalse(os.path.exists(escaped))

    def test_a_sibling_directory_sharing_a_name_prefix_is_denied(self):
        # "<tmp>/work-evil" starts with "<tmp>/work" as a string but is not
        # inside it. A startswith() check would allow this write.
        escaped = os.path.join(self.prefix_sibling, "stolen.txt")

        with self.assertRaises(WriteDenied) as ctx:
            self.writer.write(escaped, b"nope")

        self.assertEqual(ctx.exception.reason, "outside_scope")
        self.assertFalse(os.path.exists(escaped))

    def test_a_symlink_inside_the_scope_pointing_outside_is_denied(self):
        if not symlinks_available(self.tmp.name):
            self.skipTest("symlink creation not permitted on this platform/account")

        link = os.path.join(self.root, "escape_hatch")
        os.symlink(self.outside, link, target_is_directory=True)
        escaped = os.path.join(self.outside, "stolen.txt")

        with self.assertRaises(WriteDenied) as ctx:
            self.writer.write(os.path.join("escape_hatch", "stolen.txt"), b"nope")

        self.assertEqual(ctx.exception.reason, "symlink_escape")
        self.assertFalse(os.path.exists(escaped))

    def test_writing_to_the_scope_root_itself_is_denied(self):
        with self.assertRaises(WriteDenied) as ctx:
            self.writer.write(".", b"nope")
        self.assertEqual(ctx.exception.reason, "invalid_path")

    def test_an_empty_path_is_denied(self):
        with self.assertRaises(WriteDenied) as ctx:
            self.writer.write("   ", b"nope")
        self.assertEqual(ctx.exception.reason, "invalid_path")

    def test_a_denied_write_creates_no_directories_on_the_way(self):
        before = sorted(os.listdir(self.root))

        with self.assertRaises(WriteDenied):
            self.writer.write(
                os.path.join("deep", "nested", "..", "..", "..", "outside", "x.txt"),
                b"nope",
            )

        self.assertEqual(sorted(os.listdir(self.root)), before)


if __name__ == "__main__":
    unittest.main()

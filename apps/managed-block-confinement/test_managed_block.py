import os
import tempfile
import unittest

from managed_block import (
    END_MARKER,
    START_MARKER,
    ManagedWriteDenied,
    render_managed,
    write_managed_block,
)

HUMAN_ABOVE = "# Toy Repository\n\nHand-written by a person.\n\n"
HUMAN_BELOW = "\n## Notes\n\nAlso hand-written.\n"
DOCUMENT = f"{HUMAN_ABOVE}{START_MARKER}\ngenerated v1\n{END_MARKER}{HUMAN_BELOW}"


class ManagedBlockConfinementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "AGENTS.md")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, text):
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            f.write(text)

    def read(self):
        with open(self.path, "r", encoding="utf-8", newline="") as f:
            return f.read()

    def test_replacing_the_block_preserves_everything_outside_it(self):
        self.write(DOCUMENT)

        write_managed_block(self.path, "generated v2")
        result = self.read()

        self.assertTrue(result.startswith(HUMAN_ABOVE))
        self.assertTrue(result.endswith(HUMAN_BELOW))
        self.assertIn("generated v2", result)
        self.assertNotIn("generated v1", result)

    def test_content_outside_the_block_is_preserved_byte_for_byte(self):
        # CRLF endings and trailing spaces outside the block are exactly the
        # things a careless rewrite silently normalizes away.
        above = "# Toy\r\n\r\ntrailing spaces here   \r\n"
        below = "\r\n## Notes\r\n\ttab-indented\r\n"
        self.write(f"{above}{START_MARKER}\nold\n{END_MARKER}{below}")

        write_managed_block(self.path, "new")
        result = self.read()

        self.assertEqual(result[: len(above)], above)
        self.assertEqual(result[-len(below) :], below)

    def test_creating_the_block_when_none_exists_appends_it(self):
        self.write(HUMAN_ABOVE)

        write_managed_block(self.path, "first generation")
        result = self.read()

        self.assertTrue(result.startswith(HUMAN_ABOVE))
        self.assertIn(START_MARKER, result)
        self.assertIn("first generation", result)

    def test_generated_content_carrying_a_start_marker_is_refused(self):
        self.write(DOCUMENT)

        with self.assertRaises(ManagedWriteDenied) as ctx:
            write_managed_block(self.path, f"sneaky\n{START_MARKER}\nsecond block")

        self.assertEqual(ctx.exception.reason, "marker_injection")
        self.assertEqual(self.read(), DOCUMENT)  # untouched

    def test_generated_content_carrying_an_end_marker_is_refused(self):
        self.write(DOCUMENT)

        with self.assertRaises(ManagedWriteDenied) as ctx:
            write_managed_block(self.path, f"{END_MARKER}\nand then human text")

        self.assertEqual(ctx.exception.reason, "marker_injection")
        self.assertEqual(self.read(), DOCUMENT)

    def test_a_document_with_two_start_markers_fails_closed(self):
        self.write(f"{START_MARKER}\na\n{END_MARKER}\n{START_MARKER}\nb\n{END_MARKER}\n")

        with self.assertRaises(ManagedWriteDenied) as ctx:
            write_managed_block(self.path, "which block did I own?")

        self.assertEqual(ctx.exception.reason, "duplicate_markers")

    def test_an_unpaired_marker_fails_closed(self):
        self.write(f"{HUMAN_ABOVE}{START_MARKER}\ncontent with no end\n")

        with self.assertRaises(ManagedWriteDenied) as ctx:
            write_managed_block(self.path, "new")

        self.assertEqual(ctx.exception.reason, "unpaired_marker")

    def test_an_end_marker_before_its_start_fails_closed(self):
        self.write(f"{END_MARKER}\nbackwards\n{START_MARKER}\n")

        with self.assertRaises(ManagedWriteDenied) as ctx:
            write_managed_block(self.path, "new")

        self.assertEqual(ctx.exception.reason, "inverted_markers")

    def test_a_refused_render_never_opens_the_file(self):
        # render_managed is pure, so a refusal cannot leave a partial write.
        self.write(DOCUMENT)
        before = self.read()

        with self.assertRaises(ManagedWriteDenied):
            render_managed(before, f"{START_MARKER} injected")

        self.assertEqual(self.read(), before)

    def test_a_successful_write_leaves_no_temporary_file_behind(self):
        self.write(DOCUMENT)

        write_managed_block(self.path, "generated v2")

        self.assertEqual(os.listdir(self.tmp.name), ["AGENTS.md"])

    def test_repeated_writes_of_the_same_content_are_idempotent(self):
        self.write(DOCUMENT)

        once = write_managed_block(self.path, "stable content")
        twice = write_managed_block(self.path, "stable content")

        self.assertEqual(once, twice)
        self.assertEqual(twice.count(START_MARKER), 1)


if __name__ == "__main__":
    unittest.main()

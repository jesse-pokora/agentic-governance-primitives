import unittest

from anchor import Anchor, StaleInstruction, anchor, digest_of, resolve

ORIGINAL = {
    "AGENTS.md": [
        "# Toy agent instructions",
        "",
        "## Architecture",
        "Constructors receive their collaborators.",
        "Collaborators are built in the composition root.",
        "",
        "## Output",
        "Return Markdown only.",
    ]
}


class TraceableInstructionSourceTests(unittest.TestCase):
    def setUp(self):
        self.anchored = anchor(ORIGINAL, "AGENTS.md", 4, 5)

    def test_an_unchanged_source_resolves_to_the_instruction(self):
        text = resolve(self.anchored, ORIGINAL)

        self.assertIn("Constructors receive their collaborators.", text)
        self.assertIn("composition root", text)

    def test_editing_the_instruction_makes_it_stale(self):
        edited = {"AGENTS.md": list(ORIGINAL["AGENTS.md"])}
        edited["AGENTS.md"][3] = "Constructors may build their collaborators."

        with self.assertRaises(StaleInstruction) as ctx:
            resolve(self.anchored, edited)

        self.assertEqual(ctx.exception.reason, "text_changed")

    def test_inserting_a_line_above_makes_it_stale_rather_than_silently_shifting(self):
        # The trap: without the quoted text, this anchor still resolves and now
        # points at somebody else's words while looking perfectly traceable.
        shifted = {"AGENTS.md": ["## Preamble"] + list(ORIGINAL["AGENTS.md"])}

        with self.assertRaises(StaleInstruction) as ctx:
            resolve(self.anchored, shifted)

        self.assertEqual(ctx.exception.reason, "text_changed")

    def test_a_whitespace_only_change_is_still_a_change(self):
        respaced = {"AGENTS.md": list(ORIGINAL["AGENTS.md"])}
        respaced["AGENTS.md"][3] = "Constructors receive their collaborators.  "

        with self.assertRaises(StaleInstruction) as ctx:
            resolve(self.anchored, respaced)

        self.assertEqual(ctx.exception.reason, "text_changed")

    def test_a_truncated_source_is_out_of_bounds(self):
        truncated = {"AGENTS.md": ORIGINAL["AGENTS.md"][:3]}

        with self.assertRaises(StaleInstruction) as ctx:
            resolve(self.anchored, truncated)

        self.assertEqual(ctx.exception.reason, "range_out_of_bounds")

    def test_a_missing_source_file_is_refused(self):
        with self.assertRaises(StaleInstruction) as ctx:
            resolve(self.anchored, {"OTHER.md": ["something"]})

        self.assertEqual(ctx.exception.reason, "source_missing")

    def test_a_tampered_anchor_digest_is_refused(self):
        forged = Anchor(self.anchored.path, self.anchored.start_line,
                        self.anchored.end_line, self.anchored.quoted, "f" * 64)

        with self.assertRaises(StaleInstruction) as ctx:
            resolve(forged, ORIGINAL)

        self.assertEqual(ctx.exception.reason, "digest_mismatch")

    def test_an_invalid_range_is_refused(self):
        for start, end in ((0, 2), (5, 4), (-1, 3)):
            with self.subTest(start=start, end=end):
                with self.assertRaises(StaleInstruction) as ctx:
                    anchor(ORIGINAL, "AGENTS.md", start, end)
                self.assertEqual(ctx.exception.reason, "invalid_range")

    def test_the_digest_is_over_the_quoted_text(self):
        self.assertEqual(self.anchored.digest, digest_of(self.anchored.quoted))

    def test_two_anchors_over_the_same_text_agree(self):
        again = anchor(ORIGINAL, "AGENTS.md", 4, 5)

        self.assertEqual(again.digest, self.anchored.digest)
        self.assertEqual(again.quoted, self.anchored.quoted)

    def test_unrelated_edits_elsewhere_do_not_invalidate_it(self):
        elsewhere = {"AGENTS.md": list(ORIGINAL["AGENTS.md"])}
        elsewhere["AGENTS.md"][7] = "Return Markdown only, and nothing else."

        self.assertIn("composition root", resolve(self.anchored, elsewhere))


if __name__ == "__main__":
    unittest.main()

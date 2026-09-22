import unittest

from output_shape import CANONICAL_HEADINGS, OutputShapeRejected, verify_shape

GOOD = """# Repository Guide

A toy repository used for demonstration.

## Purpose

Demonstrates one governance primitive.

## Key Paths

- `apps/` one directory per demo app
"""


class CanonicalOutputShapeTests(unittest.TestCase):
    def test_a_conforming_document_is_accepted(self):
        report = verify_shape(GOOD)

        self.assertEqual(report.headings[0], "# Repository Guide")
        self.assertGreater(report.word_count, 0)

    def test_omitting_an_optional_section_entirely_is_fine(self):
        # "Architecture" and "Build and Test" are simply absent above.
        self.assertNotIn("## Architecture", verify_shape(GOOD).headings)

    def test_a_heading_with_nothing_under_it_is_rejected(self):
        with self.assertRaises(OutputShapeRejected) as ctx:
            verify_shape(GOOD + "\n## Build and Test\n\n")

        self.assertEqual(ctx.exception.reason, "empty_section")
        self.assertEqual(ctx.exception.detail, "## Build and Test")

    def test_a_near_miss_heading_spelling_is_rejected(self):
        for wrong in ("## Key paths", "## KEY PATHS", "##Key Paths", "### Key Paths"):
            with self.subTest(heading=wrong):
                document = GOOD.replace("## Key Paths", wrong)
                with self.assertRaises(OutputShapeRejected) as ctx:
                    verify_shape(document)
                self.assertIn(ctx.exception.reason,
                              {"non_canonical_heading", "missing_title",
                               "malformed_heading"})

    def test_canonical_sections_out_of_order_are_rejected(self):
        document = ("# Repository Guide\n\nintro\n\n## Key Paths\n\n- a\n\n"
                    "## Purpose\n\nwhy\n")
        with self.assertRaises(OutputShapeRejected) as ctx:
            verify_shape(document)

        self.assertEqual(ctx.exception.reason, "headings_out_of_order")

    def test_a_repeated_canonical_heading_is_rejected(self):
        document = GOOD + "\n## Purpose\n\nsaid twice\n"
        with self.assertRaises(OutputShapeRejected) as ctx:
            verify_shape(document)

        self.assertIn(ctx.exception.reason, {"headings_out_of_order", "duplicate_heading"})

    def test_a_document_wrapped_in_a_code_fence_is_rejected(self):
        with self.assertRaises(OutputShapeRejected) as ctx:
            verify_shape("```markdown\n" + GOOD + "```\n")

        self.assertEqual(ctx.exception.reason, "wrapped_in_fence")

    def test_a_fenced_block_inside_a_section_is_legitimate_content(self):
        document = GOOD + "\n## Build and Test\n\n```bash\npython -m unittest\n```\n"
        self.assertIn("## Build and Test", verify_shape(document).headings)

    def test_a_missing_title_is_rejected(self):
        with self.assertRaises(OutputShapeRejected) as ctx:
            verify_shape("## Purpose\n\nno title above me\n")

        self.assertEqual(ctx.exception.reason, "missing_title")

    def test_output_over_the_word_bound_is_rejected(self):
        padded = GOOD + "\n## Build and Test\n\n" + ("word " * 200)
        with self.assertRaises(OutputShapeRejected) as ctx:
            verify_shape(padded, max_words=50)

        self.assertEqual(ctx.exception.reason, "too_long")

    def test_empty_output_is_rejected(self):
        with self.assertRaises(OutputShapeRejected) as ctx:
            verify_shape("   \n\n")

        self.assertEqual(ctx.exception.reason, "empty_output")

    def test_the_checker_never_repairs_its_input(self):
        document = GOOD
        try:
            verify_shape(document)
        except OutputShapeRejected:
            pass
        self.assertEqual(document, GOOD)
        self.assertEqual(len(CANONICAL_HEADINGS), 6)


if __name__ == "__main__":
    unittest.main()

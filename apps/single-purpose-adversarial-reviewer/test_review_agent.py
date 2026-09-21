import inspect
import unittest

import review_agent
from review_agent import InvalidReviewPayload, review


class SinglePurposeAdversarialReviewerTests(unittest.TestCase):
    def test_flags_eval_usage(self):
        result = review({"artifact_id": "toy-1", "content": "x = eval(user_input)"})
        severities = {f["severity"] for f in result["findings"]}
        self.assertIn("high", severities)

    def test_flags_hardcoded_password_like_string(self):
        result = review({"artifact_id": "toy-2", "content": "PASSWORD = 'abc123'"})
        severities = {f["severity"] for f in result["findings"]}
        self.assertIn("medium", severities)

    def test_clean_content_produces_no_findings(self):
        result = review({"artifact_id": "toy-3", "content": "def add(a, b): return a + b"})
        self.assertEqual(result["findings"], [])

    def test_output_matches_the_fixed_schema_shape(self):
        result = review({"artifact_id": "toy-4", "content": "eval(x)"})
        self.assertEqual(set(result.keys()), {"artifact_id", "findings"})
        for finding in result["findings"]:
            self.assertEqual(set(finding.keys()), {"severity", "description"})

    def test_invalid_input_shape_is_rejected(self):
        with self.assertRaises(InvalidReviewPayload):
            review({"artifact_id": "toy-5"})  # missing "content"

    def test_repeated_calls_with_the_same_input_are_pure_and_identical(self):
        payload = {"artifact_id": "toy-6", "content": "eval(x); PASSWORD='y'"}
        results = [review(payload) for _ in range(10)]
        self.assertTrue(all(r == results[0] for r in results))

    def test_calling_order_across_different_inputs_never_leaks_state(self):
        clean = {"artifact_id": "toy-7", "content": "safe code"}
        dirty = {"artifact_id": "toy-8", "content": "eval(x)"}

        review(dirty)
        result_after_dirty = review(clean)
        self.assertEqual(result_after_dirty["findings"], [])

    def test_module_exposes_exactly_one_public_callable(self):
        public_names = [
            name
            for name, value in vars(review_agent).items()
            if not name.startswith("_") and inspect.isfunction(value)
        ]
        self.assertEqual(public_names, ["review"])


if __name__ == "__main__":
    unittest.main()

import unittest

from fingerprint import SourceRejected, duplicates, fingerprints

EXISTING = """
def normalize_path(raw):
    cleaned = raw.strip()
    if not cleaned:
        return None
    return cleaned.lower()
"""

# What an agent writes when it has forgotten the above exists.
REIMPLEMENTED = """
def tidy_path_value(value):
    trimmed = value.strip()
    if not trimmed:
        return None
    return trimmed.lower()
"""

DIFFERENT = """
def normalize_path(raw):
    return raw.replace("\\\\", "/")
"""


def one(source):
    return fingerprints(source)[0].fingerprint


class StructuralDuplicateTests(unittest.TestCase):
    def test_the_same_implementation_under_a_new_name_matches(self):
        self.assertEqual(one(EXISTING), one(REIMPLEMENTED))

    def test_a_genuinely_different_implementation_does_not_match(self):
        self.assertNotEqual(one(EXISTING), one(DIFFERENT))

    def test_renaming_only_the_parameters_does_not_change_the_shape(self):
        a = "def f(alpha, beta):\n    return alpha + beta\n"
        b = "def g(x, y):\n    return x + y\n"

        self.assertEqual(one(a), one(b))

    def test_adding_a_docstring_does_not_change_the_shape(self):
        with_doc = '''def f(x):
    """Explains the thing."""
    return x + 1
'''
        self.assertEqual(one("def f(x):\n    return x + 1\n"), one(with_doc))

    def test_a_different_literal_is_a_different_function(self):
        # Two functions differing only in a constant are doing different
        # things; saying otherwise would make the fingerprint lie.
        self.assertNotEqual(one("def f(x):\n    return x + 1\n"),
                            one("def f(x):\n    return x + 2\n"))

    def test_a_different_operator_is_a_different_function(self):
        self.assertNotEqual(one("def f(x, y):\n    return x + y\n"),
                            one("def f(x, y):\n    return x - y\n"))

    def test_calling_a_different_helper_is_a_different_function(self):
        self.assertNotEqual(one("def f(x):\n    return clean(x)\n"),
                            one("def f(x):\n    return scrub(x)\n"))

    def test_duplicates_across_two_modules_are_grouped(self):
        groups = duplicates(EXISTING, REIMPLEMENTED)

        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(item.name for item in groups[0]),
                         ["normalize_path", "tidy_path_value"])

    def test_a_function_with_no_twin_is_not_reported(self):
        self.assertEqual(duplicates(EXISTING, DIFFERENT), ())

    def test_duplicates_within_one_module_are_found(self):
        merged = EXISTING + REIMPLEMENTED

        self.assertEqual(len(duplicates(merged)), 1)

    def test_nested_functions_are_fingerprinted_too(self):
        source = "def outer():\n    def inner(x):\n        return x + 1\n    return inner\n"

        self.assertEqual(len(fingerprints(source)), 2)

    def test_the_report_is_stable_across_runs(self):
        first = duplicates(EXISTING, REIMPLEMENTED)
        second = duplicates(EXISTING, REIMPLEMENTED)

        self.assertEqual([tuple(i.fingerprint for i in g) for g in first],
                         [tuple(i.fingerprint for i in g) for g in second])

    def test_unparseable_source_is_refused(self):
        with self.assertRaises(SourceRejected) as ctx:
            fingerprints("def f(:\n")

        self.assertEqual(ctx.exception.reason, "parse_error")

    def test_comparing_nothing_is_refused(self):
        with self.assertRaises(SourceRejected) as ctx:
            duplicates()

        self.assertEqual(ctx.exception.reason, "no_sources")


if __name__ == "__main__":
    unittest.main()

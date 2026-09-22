import unittest

from admission_gate import AdmissionDenied, AdmissionPolicy, admit_and_run

POLICY = AdmissionPolicy.of(
    imports={"math"},
    calls={"record", "len", "math.sqrt"},
)


class Spy:
    """Observable side effect: proves whether denied code ever ran."""

    def __init__(self):
        self.calls = []

    def __call__(self, value):
        self.calls.append(value)
        return value


class GeneratedCodeAdmissionGateTests(unittest.TestCase):
    def setUp(self):
        self.spy = Spy()
        self.namespace = {"record": self.spy}

    def run_source(self, source, policy=POLICY):
        return admit_and_run(source, policy, dict(self.namespace))

    def test_admitted_code_runs(self):
        result = self.run_source("total = len([1, 2, 3])\nrecord(total)\n")

        self.assertEqual(result["total"], 3)
        self.assertEqual(self.spy.calls, [3])

    def test_an_allowed_import_is_usable(self):
        result = self.run_source("import math\nroot = math.sqrt(9)\n")

        self.assertEqual(result["root"], 3.0)

    def test_an_undeclared_import_is_denied_and_the_program_never_runs(self):
        # The record() call is on line 1, before the offending import. The gate
        # admits whole programs, not lines, so nothing runs at all.
        source = "record('side effect')\nimport os\n"

        with self.assertRaises(AdmissionDenied) as ctx:
            self.run_source(source)

        self.assertEqual(ctx.exception.reason, "import_not_allowed")
        self.assertEqual(ctx.exception.detail, "os")
        self.assertEqual(self.spy.calls, [])

    def test_the_dunder_import_bypass_is_denied(self):
        # A denylist matching the word "import" at line start misses this.
        with self.assertRaises(AdmissionDenied) as ctx:
            self.run_source("os = __import__('os')\n")

        self.assertEqual(ctx.exception.reason, "forbidden_name")
        self.assertEqual(self.spy.calls, [])

    def test_the_dunder_class_escape_chain_is_denied(self):
        # The standard route out of a restricted namespace: reach every loaded
        # class without importing anything.
        source = "leaked = ().__class__.__bases__[0].__subclasses__()\n"

        with self.assertRaises(AdmissionDenied) as ctx:
            self.run_source(source)

        self.assertEqual(ctx.exception.reason, "dunder_access")

    def test_a_policy_cannot_allowlist_its_way_past_eval(self):
        permissive = AdmissionPolicy.of(imports=set(), calls={"eval", "record"})

        with self.assertRaises(AdmissionDenied) as ctx:
            self.run_source("record(eval('1+1'))\n", policy=permissive)

        self.assertEqual(ctx.exception.reason, "forbidden_name")
        self.assertEqual(ctx.exception.detail, "eval")
        self.assertEqual(self.spy.calls, [])

    def test_an_undeclared_call_is_denied(self):
        with self.assertRaises(AdmissionDenied) as ctx:
            self.run_source("record(sorted([3, 1, 2]))\n")

        self.assertEqual(ctx.exception.reason, "call_not_allowed")
        self.assertEqual(ctx.exception.detail, "sorted")

    def test_a_call_the_gate_cannot_resolve_statically_is_denied(self):
        with self.assertRaises(AdmissionDenied) as ctx:
            self.run_source("handlers = []\nrecord(handlers[0]())\n")

        self.assertEqual(ctx.exception.reason, "unresolvable_call")

    def test_a_forbidden_name_inside_a_string_is_not_a_call(self):
        # The test that separates parsing from pattern matching: a denylist
        # grepping for "import os" or "eval(" rejects this admissible program.
        source = 'banner = "import os and eval() are not allowed"\nrecord(banner)\n'

        result = self.run_source(source)

        self.assertIn("import os", result["banner"])
        self.assertEqual(len(self.spy.calls), 1)

    def test_unparseable_source_is_denied_before_anything_runs(self):
        with self.assertRaises(AdmissionDenied) as ctx:
            self.run_source("record('x'\n")

        self.assertEqual(ctx.exception.reason, "parse_error")
        self.assertEqual(self.spy.calls, [])

    def test_the_earliest_violation_in_source_order_is_the_one_reported(self):
        source = "import socket\nos = __import__('os')\n"

        with self.assertRaises(AdmissionDenied) as ctx:
            self.run_source(source)

        self.assertEqual(ctx.exception.reason, "import_not_allowed")
        self.assertEqual(ctx.exception.lineno, 1)


if __name__ == "__main__":
    unittest.main()

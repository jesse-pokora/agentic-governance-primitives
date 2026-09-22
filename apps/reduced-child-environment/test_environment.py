import os
import sys
import unittest

from environment import (
    EnvironmentDenied, EnvironmentPolicy, build_child_environment, run,
)

DUMP_ENV = "import os, json; print(json.dumps(dict(os.environ)))"

PARENT = {
    "PATH": os.environ.get("PATH", ""),
    "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    "MODEL_ENDPOINT": "https://api.example.test",
    "AWS_SECRET_ACCESS_KEY": "toy-secret-AAAA1111",
    "GITHUB_TOKEN": "toy-ghp-BBBB2222",
    "OPERATOR_SSH_KEY": "-----BEGIN PRIVATE KEY-----",
    "SOME_FUTURE_SECRET": "nobody wrote a rule for this one",
}
POLICY = EnvironmentPolicy.of(passthrough={"MODEL_ENDPOINT"})


class ReducedChildEnvironmentTests(unittest.TestCase):
    def test_a_passthrough_variable_reaches_the_child(self):
        child = build_child_environment(PARENT, POLICY)
        self.assertEqual(child["MODEL_ENDPOINT"], "https://api.example.test")

    def test_seeded_secrets_are_absent_not_redacted(self):
        child = build_child_environment(PARENT, POLICY)

        for secret in ("AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN", "OPERATOR_SSH_KEY"):
            self.assertNotIn(secret, child)
        self.assertNotIn("toy-secret-AAAA1111", "".join(child.values()))

    def test_a_secret_nobody_wrote_a_rule_for_is_also_absent(self):
        # The property an allowlist has and a denylist cannot: it covers the
        # variables that did not exist when the policy was written.
        child = build_child_environment(PARENT, POLICY)
        self.assertNotIn("SOME_FUTURE_SECRET", child)

    def test_platform_essentials_pass_through_by_declaration(self):
        child = build_child_environment(PARENT, POLICY)
        self.assertIn("PATH", child)

    def test_platform_essentials_can_be_declined(self):
        child = build_child_environment(
            PARENT, EnvironmentPolicy.of({"MODEL_ENDPOINT"}, include_platform_essentials=False)
        )
        self.assertEqual(set(child), {"MODEL_ENDPOINT"})

    def test_injected_values_are_added(self):
        child = build_child_environment(
            PARENT, EnvironmentPolicy.of({"MODEL_ENDPOINT"}, injected={"RUN_ID": "r-1"})
        )
        self.assertEqual(child["RUN_ID"], "r-1")

    def test_an_injection_colliding_with_a_passthrough_is_refused(self):
        with self.assertRaises(EnvironmentDenied) as ctx:
            build_child_environment(
                PARENT,
                EnvironmentPolicy.of({"MODEL_ENDPOINT"},
                                     injected={"MODEL_ENDPOINT": "https://other.test"}),
            )

        self.assertEqual(ctx.exception.reason, "injection_collides_with_passthrough")

    def test_a_real_child_process_cannot_see_the_secrets(self):
        result = run(sys.executable, ["-c", DUMP_ENV], PARENT, POLICY)

        self.assertEqual(result.returncode, 0)
        self.assertNotIn("toy-secret-AAAA1111", result.stdout)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", result.stdout)
        self.assertIn("MODEL_ENDPOINT", result.stdout)

    def test_the_child_does_not_inherit_this_test_process_environment(self):
        os.environ["LEAKED_FROM_PARENT"] = "toy-should-not-appear"
        try:
            result = run(sys.executable, ["-c", DUMP_ENV], PARENT, POLICY)
            self.assertNotIn("LEAKED_FROM_PARENT", result.stdout)
        finally:
            del os.environ["LEAKED_FROM_PARENT"]


if __name__ == "__main__":
    unittest.main()

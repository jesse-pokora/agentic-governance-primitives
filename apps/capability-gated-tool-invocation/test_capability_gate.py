import unittest

from capability_gate import CapabilityDenied, CapabilityGate, ToolSpec


class SpyTool:
    """Records every entry into the tool body, so a denial that still ran the
    tool is visible as a non-zero call count."""

    def __init__(self, result="toy-result"):
        self.calls = 0
        self.result = result

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.result


class CapabilityGatedToolInvocationTests(unittest.TestCase):
    def setUp(self):
        self.read_repo = SpyTool("toy file contents")
        self.read_secrets = SpyTool("toy secret material")
        self.deploy = SpyTool("toy deploy receipt")

        self.personas = {
            "reviewer": {"repo.read"},
            "release-agent": {"repo.read", "deploy.execute"},
        }
        self.tools = {
            "read_repo": ToolSpec("read_repo", "repo.read", self.read_repo),
            "read_secrets": ToolSpec("read_secrets", "repo.read_secrets", self.read_secrets),
            "deploy": ToolSpec("deploy", "deploy.execute", self.deploy),
        }
        self.gate = CapabilityGate(self.personas, self.tools)

    def test_granted_capability_invokes_the_tool(self):
        self.assertEqual(self.gate.invoke("reviewer", "read_repo"), "toy file contents")
        self.assertEqual(self.read_repo.calls, 1)

    def test_ungranted_capability_is_denied_before_the_tool_body_runs(self):
        with self.assertRaises(CapabilityDenied) as ctx:
            self.gate.invoke("reviewer", "deploy")

        self.assertEqual(ctx.exception.reason, "capability_not_granted")
        self.assertEqual(self.deploy.calls, 0)

    def test_a_capability_prefix_does_not_imply_the_longer_capability(self):
        # "reviewer" holds repo.read; read_secrets requires repo.read_secrets.
        with self.assertRaises(CapabilityDenied) as ctx:
            self.gate.invoke("reviewer", "read_secrets")

        self.assertEqual(ctx.exception.reason, "capability_not_granted")
        self.assertEqual(self.read_secrets.calls, 0)

    def test_a_wildcard_string_grants_nothing(self):
        gate = CapabilityGate({"wildcard-persona": {"repo.*"}}, self.tools)

        with self.assertRaises(CapabilityDenied) as ctx:
            gate.invoke("wildcard-persona", "read_repo")

        self.assertEqual(ctx.exception.reason, "capability_not_granted")
        self.assertEqual(self.read_repo.calls, 0)

    def test_unknown_persona_is_denied(self):
        with self.assertRaises(CapabilityDenied) as ctx:
            self.gate.invoke("ghost-persona", "read_repo")

        self.assertEqual(ctx.exception.reason, "unknown_persona")
        self.assertEqual(self.read_repo.calls, 0)

    def test_unknown_tool_is_denied(self):
        with self.assertRaises(CapabilityDenied) as ctx:
            self.gate.invoke("release-agent", "rm_rf")

        self.assertEqual(ctx.exception.reason, "unknown_tool")

    def test_mutating_the_source_catalog_after_construction_grants_nothing(self):
        # Runtime escalation attempt: the caller's dict is not the authority.
        self.personas["reviewer"].add("deploy.execute")

        with self.assertRaises(CapabilityDenied) as ctx:
            self.gate.invoke("reviewer", "deploy")

        self.assertEqual(ctx.exception.reason, "capability_not_granted")
        self.assertEqual(self.deploy.calls, 0)

    def test_granted_set_is_immutable_to_its_holder(self):
        granted = self.gate.capabilities_of("reviewer")
        with self.assertRaises(AttributeError):
            granted.add("deploy.execute")


if __name__ == "__main__":
    unittest.main()

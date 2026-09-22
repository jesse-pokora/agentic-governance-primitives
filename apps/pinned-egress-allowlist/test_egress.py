import unittest

from egress import EgressDenied, PinnedEgressAllowlist


class PinnedEgressAllowlistTests(unittest.TestCase):
    def setUp(self):
        self.allowlist = PinnedEgressAllowlist(
            ["https://api.example.test", "https://mirror.example.test:8443"]
        )

    def test_allowlisted_host_on_its_default_port_is_allowed(self):
        target = self.allowlist.check("https://api.example.test/v1/toy")
        self.assertEqual(target.host, "api.example.test")
        self.assertEqual(target.port, 443)

    def test_the_implicit_and_explicit_default_port_are_the_same_target(self):
        implicit = self.allowlist.check("https://api.example.test/v1/toy")
        explicit = self.allowlist.check("https://api.example.test:443/v1/toy")
        self.assertEqual(implicit, explicit)

    def test_an_unlisted_port_on_an_allowlisted_host_is_denied(self):
        with self.assertRaises(EgressDenied) as ctx:
            self.allowlist.check("https://api.example.test:8443/v1/toy")
        self.assertEqual(ctx.exception.reason, "port_not_allowed")

    def test_a_suffix_lookalike_host_is_denied(self):
        # Contains the allowlisted name as a prefix; is a different host.
        with self.assertRaises(EgressDenied) as ctx:
            self.allowlist.check("https://api.example.test.evil.test/v1/toy")
        self.assertEqual(ctx.exception.reason, "host_not_allowed")
        self.assertEqual(ctx.exception.detail, "api.example.test.evil.test")

    def test_a_userinfo_prefix_cannot_disguise_the_real_host(self):
        with self.assertRaises(EgressDenied) as ctx:
            self.allowlist.check("https://api.example.test@evil.test/v1/toy")
        self.assertEqual(ctx.exception.reason, "userinfo_not_allowed")

    def test_host_matching_is_case_insensitive_and_ignores_the_root_dot(self):
        for url in (
            "https://API.Example.TEST/v1/toy",
            "https://api.example.test./v1/toy",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.allowlist.check(url).host, "api.example.test")

    def test_an_ip_literal_for_an_allowlisted_name_is_denied(self):
        with self.assertRaises(EgressDenied) as ctx:
            self.allowlist.check("https://203.0.113.10/v1/toy")
        self.assertEqual(ctx.exception.reason, "host_not_allowed")

    def test_a_non_allowlisted_scheme_is_denied(self):
        with self.assertRaises(EgressDenied) as ctx:
            self.allowlist.check("file:///etc/toy-secrets")
        self.assertEqual(ctx.exception.reason, "scheme_not_allowed")

    def test_a_malformed_url_is_denied(self):
        for url in ("api.example.test/v1", "https://api.example.test:99999/v1"):
            with self.subTest(url=url):
                with self.assertRaises(EgressDenied) as ctx:
                    self.allowlist.check(url)
                self.assertEqual(ctx.exception.reason, "malformed_url")

    def test_a_fully_allowlisted_redirect_chain_is_allowed(self):
        target = self.allowlist.check_chain(
            [
                "https://api.example.test/v1/toy",
                "https://mirror.example.test:8443/v1/toy",
            ]
        )
        self.assertEqual(target.host, "mirror.example.test")
        self.assertEqual(target.port, 8443)

    def test_a_redirect_to_an_unlisted_host_is_denied_naming_the_hop(self):
        with self.assertRaises(EgressDenied) as ctx:
            self.allowlist.check_chain(
                [
                    "https://api.example.test/v1/toy",  # allowed first hop
                    "https://exfil.evil.test/collect",  # 302 lands here
                ]
            )
        self.assertEqual(ctx.exception.reason, "host_not_allowed")
        self.assertIn("hop=1", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()

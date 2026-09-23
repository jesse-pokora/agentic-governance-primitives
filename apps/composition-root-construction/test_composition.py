import unittest

from composition import Policy, SourceRejected, check

POLICY = Policy.of(
    collaborators={"SqlRepository", "HttpClient", "Mailer"},
    composition_root={"compose", "main"},
)

INJECTED = """
class Service:
    def __init__(self, repo, mailer):
        self.repo = repo
        self.mailer = mailer

    def run(self):
        return self.repo.load()


def compose():
    return Service(SqlRepository(), Mailer())
"""

SELF_CONSTRUCTED = """
class Service:
    def __init__(self):
        self.repo = SqlRepository()
"""


class CompositionRootTests(unittest.TestCase):
    def test_collaborators_wired_in_the_composition_root_pass(self):
        verdict, detail = check(INJECTED, POLICY)

        self.assertEqual(verdict, "passed")
        self.assertIn("2 construction", detail)

    def test_a_class_building_its_own_collaborator_fails(self):
        verdict, detail = check(SELF_CONSTRUCTED, POLICY)

        self.assertEqual(verdict, "failed")
        self.assertIn("SqlRepository", detail)
        self.assertIn("Service.__init__", detail)

    def test_construction_in_any_other_method_also_fails(self):
        source = """
class Service:
    def __init__(self, repo):
        self.repo = repo

    def refresh(self):
        self.client = HttpClient()
"""
        verdict, detail = check(source, POLICY)

        self.assertEqual(verdict, "failed")
        self.assertIn("Service.refresh", detail)

    def test_a_module_level_singleton_fails(self):
        # The sneakiest shape: the class looks injected, and the wiring has
        # just moved up one line out of sight.
        source = "REPO = SqlRepository()\n\nclass Service:\n    def run(self):\n        return REPO\n"

        verdict, detail = check(source, POLICY)

        self.assertEqual(verdict, "failed")
        self.assertIn("<module>", detail)

    def test_construction_in_a_default_argument_fails(self):
        source = "def handler(repo=SqlRepository()):\n    return repo\n"

        verdict, detail = check(source, POLICY)

        self.assertEqual(verdict, "failed")
        self.assertIn("handler", detail)

    def test_constructing_something_undeclared_is_not_a_violation(self):
        source = """
class Service:
    def __init__(self, repo):
        self.repo = repo
        self.items = []
        self.total = Decimal("1.00")
"""
        self.assertEqual(check(source, POLICY)[0], "not_applicable")

    def test_source_that_never_mentions_a_collaborator_is_not_applicable(self):
        verdict, detail = check("def add(a, b):\n    return a + b\n", POLICY)

        self.assertEqual(verdict, "not_applicable")
        self.assertIn("no declared collaborator", detail)

    def test_mentioning_a_collaborator_without_constructing_it_passes(self):
        # A type annotation or an isinstance check is a mention, not a wiring.
        source = "def handle(repo: SqlRepository):\n    return repo.load()\n"

        self.assertEqual(check(source, POLICY)[0], "passed")

    def test_every_offending_site_is_reported_not_just_the_first(self):
        source = """
class A:
    def __init__(self):
        self.repo = SqlRepository()

class B:
    def __init__(self):
        self.mail = Mailer()
"""
        verdict, detail = check(source, POLICY)

        self.assertEqual(verdict, "failed")
        self.assertIn("A.__init__", detail)
        self.assertIn("B.__init__", detail)

    def test_unparseable_source_is_refused(self):
        with self.assertRaises(SourceRejected) as ctx:
            check("class Service(\n", POLICY)

        self.assertEqual(ctx.exception.reason, "parse_error")

    def test_a_policy_with_no_composition_root_is_refused(self):
        with self.assertRaises(SourceRejected) as ctx:
            Policy.of(collaborators={"SqlRepository"}, composition_root=set())

        self.assertEqual(ctx.exception.reason, "no_composition_root")

    def test_a_policy_declaring_no_collaborators_is_refused(self):
        with self.assertRaises(SourceRejected) as ctx:
            Policy.of(collaborators=set(), composition_root={"compose"})

        self.assertEqual(ctx.exception.reason, "no_collaborators_declared")


if __name__ == "__main__":
    unittest.main()

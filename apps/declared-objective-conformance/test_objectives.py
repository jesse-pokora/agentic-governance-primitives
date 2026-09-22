import unittest

from objectives import Action, ObjectiveViolation, Run

DECLARED = {"summarize-repository", "record-evidence"}


class Spy:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return "done"


class DeclaredObjectiveConformanceTests(unittest.TestCase):
    def setUp(self):
        self.run = Run.declaring(set(DECLARED))
        self.spy = Spy()

    def test_an_action_citing_a_declared_objective_runs(self):
        result = self.run.perform(
            Action("read_repo", ("summarize-repository",)), self.spy
        )

        self.assertEqual(result, "done")
        self.assertEqual(self.spy.calls, 1)

    def test_an_action_citing_nothing_is_refused_before_it_runs(self):
        with self.assertRaises(ObjectiveViolation) as ctx:
            self.run.perform(Action("open_pull_request", ()), self.spy)

        self.assertEqual(ctx.exception.reason, "uncited_action")
        self.assertEqual(self.spy.calls, 0)

    def test_an_action_citing_an_undeclared_objective_is_refused(self):
        with self.assertRaises(ObjectiveViolation) as ctx:
            self.run.perform(
                Action("deploy", ("improve-deployment-speed",)), self.spy
            )

        self.assertEqual(ctx.exception.reason, "undeclared_objective")
        self.assertIn("improve-deployment-speed", ctx.exception.detail)
        self.assertEqual(self.spy.calls, 0)

    def test_one_undeclared_objective_taints_an_otherwise_valid_action(self):
        with self.assertRaises(ObjectiveViolation) as ctx:
            self.run.perform(
                Action("deploy", ("summarize-repository", "ship-it")), self.spy
            )

        self.assertEqual(ctx.exception.reason, "undeclared_objective")
        self.assertEqual(self.spy.calls, 0)

    def test_every_undeclared_objective_is_named(self):
        with self.assertRaises(ObjectiveViolation) as ctx:
            self.run.perform(Action("drift", ("alpha", "beta")), self.spy)

        self.assertIn("alpha", ctx.exception.detail)
        self.assertIn("beta", ctx.exception.detail)

    def test_an_action_may_serve_several_declared_objectives(self):
        self.run.perform(
            Action("write_evidence", ("summarize-repository", "record-evidence")),
            self.spy,
        )

        self.assertEqual(self.spy.calls, 1)

    def test_widening_the_source_set_after_declaring_grants_nothing(self):
        source = set(DECLARED)
        run = Run.declaring(source)
        source.add("deploy-to-production")

        with self.assertRaises(ObjectiveViolation) as ctx:
            run.perform(Action("deploy", ("deploy-to-production",)), self.spy)

        self.assertEqual(ctx.exception.reason, "undeclared_objective")

    def test_the_declared_set_is_immutable_to_its_holder(self):
        with self.assertRaises(AttributeError):
            self.run.objectives.add("deploy-to-production")

    def test_a_run_must_declare_at_least_one_objective(self):
        with self.assertRaises(ObjectiveViolation) as ctx:
            Run.declaring(set())

        self.assertEqual(ctx.exception.reason, "no_objectives")

    def test_a_declared_objective_that_nothing_served_is_not_a_violation(self):
        self.run.perform(Action("read_repo", ("summarize-repository",)), self.spy)

        self.assertEqual(self.run.objectives_served(), frozenset({"summarize-repository"}))
        self.assertIn("record-evidence", self.run.objectives)

    def test_only_performed_actions_are_recorded(self):
        self.run.perform(Action("read_repo", ("summarize-repository",)), self.spy)
        with self.assertRaises(ObjectiveViolation):
            self.run.perform(Action("deploy", ("ship-it",)), self.spy)

        self.assertEqual([a.name for a in self.run.performed], ["read_repo"])


if __name__ == "__main__":
    unittest.main()

import unittest

from separation import Approval, ApprovalDenied, Artifact, accept

CONTENT = {"guide": "toy repository guide", "version": 1}
REVISED = {"guide": "toy repository guide, revised", "version": 2}


class ProducerApproverSeparationTests(unittest.TestCase):
    def setUp(self):
        self.artifact = Artifact(produced_by="toy-writer-agent", content=CONTENT)

    def test_an_independent_approver_naming_the_exact_digest_is_accepted(self):
        accepted = accept(
            self.artifact,
            Approval(approved_by="toy-human-reviewer", artifact_digest=self.artifact.digest),
        )

        self.assertEqual(accepted.produced_by, "toy-writer-agent")
        self.assertEqual(accepted.approved_by, "toy-human-reviewer")

    def test_the_producer_cannot_approve_its_own_artifact(self):
        with self.assertRaises(ApprovalDenied) as ctx:
            accept(self.artifact,
                   Approval(approved_by="toy-writer-agent", artifact_digest=self.artifact.digest))

        self.assertEqual(ctx.exception.reason, "self_approval")

    def test_respelling_the_producer_name_does_not_create_independence(self):
        for alias in ("Toy-Writer-Agent", "  toy-writer-agent  ", "TOY-WRITER-AGENT"):
            with self.subTest(alias=alias):
                with self.assertRaises(ApprovalDenied) as ctx:
                    accept(self.artifact,
                           Approval(approved_by=alias, artifact_digest=self.artifact.digest))
                self.assertEqual(ctx.exception.reason, "self_approval")

    def test_approving_through_a_delegate_is_still_self_approval(self):
        with self.assertRaises(ApprovalDenied) as ctx:
            accept(
                self.artifact,
                Approval(approved_by="ci-service-account", artifact_digest=self.artifact.digest),
                delegates={"ci-service-account": "toy-writer-agent"},
            )

        self.assertEqual(ctx.exception.reason, "self_approval")

    def test_an_approval_of_a_different_artifact_does_not_carry_over(self):
        stale = Approval(approved_by="toy-human-reviewer",
                         artifact_digest=Artifact("toy-writer-agent", REVISED).digest)

        with self.assertRaises(ApprovalDenied) as ctx:
            accept(self.artifact, stale)

        self.assertEqual(ctx.exception.reason, "approval_not_bound")

    def test_an_approval_does_not_survive_the_artifact_changing(self):
        approval = Approval(approved_by="toy-human-reviewer",
                            artifact_digest=self.artifact.digest)
        revised = Artifact(produced_by="toy-writer-agent", content=REVISED)

        with self.assertRaises(ApprovalDenied) as ctx:
            accept(revised, approval)

        self.assertEqual(ctx.exception.reason, "approval_not_bound")

    def test_an_unnamed_producer_is_refused(self):
        with self.assertRaises(ApprovalDenied) as ctx:
            accept(Artifact(produced_by="   ", content=CONTENT),
                   Approval(approved_by="toy-human-reviewer",
                            artifact_digest=self.artifact.digest))

        self.assertEqual(ctx.exception.reason, "unattributed_artifact")

    def test_an_unnamed_approver_is_refused(self):
        with self.assertRaises(ApprovalDenied) as ctx:
            accept(self.artifact,
                   Approval(approved_by="", artifact_digest=self.artifact.digest))

        self.assertEqual(ctx.exception.reason, "unattributed_approval")

    def test_a_different_delegate_principal_is_genuinely_independent(self):
        accepted = accept(
            self.artifact,
            Approval(approved_by="ci-service-account", artifact_digest=self.artifact.digest),
            delegates={"ci-service-account": "toy-human-reviewer"},
        )

        self.assertEqual(accepted.approved_by, "ci-service-account")


if __name__ == "__main__":
    unittest.main()

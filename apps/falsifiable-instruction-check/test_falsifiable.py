import unittest

from falsifiable import Candidate, NotFalsifiable, Registry, register

# The instruction: a module must not call eval().
SOUND = Candidate(
    id="INS-010",
    text="Generated modules must not call eval()",
    check=lambda source: "eval(" not in source,
    violating="result = eval(user_input)\n",
    satisfying="result = int(user_input)\n",
)


class FalsifiableInstructionTests(unittest.TestCase):
    def test_a_checker_that_discriminates_is_registered(self):
        instruction = register(SOUND)

        self.assertEqual(instruction.id, "INS-010")
        self.assertFalse(instruction.check(instruction.violating))
        self.assertTrue(instruction.check(instruction.satisfying))

    def test_a_checker_that_accepts_everything_is_refused(self):
        vacuous = Candidate("INS-011", "anything goes", lambda source: True,
                            violating=SOUND.violating, satisfying=SOUND.satisfying)

        with self.assertRaises(NotFalsifiable) as ctx:
            register(vacuous)

        self.assertEqual(ctx.exception.reason, "checker_accepts_violation")

    def test_a_checker_that_rejects_everything_is_refused(self):
        # Not vacuous, but useless in the other direction: it would fail every
        # artifact and be switched off within a day.
        paranoid = Candidate("INS-012", "nothing goes", lambda source: False,
                             violating=SOUND.violating, satisfying=SOUND.satisfying)

        with self.assertRaises(NotFalsifiable) as ctx:
            register(paranoid)

        self.assertEqual(ctx.exception.reason, "checker_rejects_satisfying")

    def test_a_subtly_wrong_checker_is_caught(self):
        # Looks right, matches nothing: the real shape of this bug.
        typo = Candidate("INS-013", "no eval", lambda source: "evaluate(" not in source,
                         violating=SOUND.violating, satisfying=SOUND.satisfying)

        with self.assertRaises(NotFalsifiable) as ctx:
            register(typo)

        self.assertEqual(ctx.exception.reason, "checker_accepts_violation")

    def test_an_instruction_with_no_violating_fixture_is_refused(self):
        with self.assertRaises(NotFalsifiable) as ctx:
            register(Candidate("INS-014", "no eval", lambda s: "eval(" not in s,
                               satisfying=SOUND.satisfying))

        self.assertEqual(ctx.exception.reason, "missing_violating_fixture")

    def test_an_instruction_with_no_satisfying_fixture_is_refused(self):
        with self.assertRaises(NotFalsifiable) as ctx:
            register(Candidate("INS-015", "no eval", lambda s: "eval(" not in s,
                               violating=SOUND.violating))

        self.assertEqual(ctx.exception.reason, "missing_satisfying_fixture")

    def test_a_checker_that_raises_is_refused_naming_the_fixture(self):
        def explodes(source):
            raise RuntimeError("toy checker bug")

        with self.assertRaises(NotFalsifiable) as ctx:
            register(Candidate("INS-016", "no eval", explodes,
                               violating=SOUND.violating, satisfying=SOUND.satisfying))

        self.assertEqual(ctx.exception.reason, "checker_errored")
        self.assertIn("violating", ctx.exception.detail)

    def test_the_fixtures_stay_attached_to_the_registered_instruction(self):
        # The evidence that this checker can fail travels with it, so the claim
        # can be re-verified later rather than taken on trust.
        instruction = register(SOUND)

        self.assertEqual(instruction.violating, SOUND.violating)
        self.assertEqual(instruction.satisfying, SOUND.satisfying)

    def test_a_registry_admits_only_falsifiable_instructions(self):
        registry = Registry()
        registry.add(SOUND)

        with self.assertRaises(NotFalsifiable):
            registry.add(Candidate("INS-017", "anything", lambda s: True,
                                   violating=SOUND.violating, satisfying=SOUND.satisfying))

        self.assertEqual(registry.ids(), ("INS-010",))

    def test_a_duplicate_instruction_id_is_refused(self):
        registry = Registry()
        registry.add(SOUND)

        with self.assertRaises(NotFalsifiable) as ctx:
            registry.add(SOUND)

        self.assertEqual(ctx.exception.reason, "duplicate_instruction_id")


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest

from dry_run import EffectDenied, Executor, PlannedEffect


def do_work(executor, path, index_path):
    """One routine, used for both modes. There is no dry-run branch in here."""
    executor.perform(
        PlannedEffect("write", path, "managed guide, 3 sections"),
        lambda: _write(path, "generated guide\n"),
    )
    executor.perform(
        PlannedEffect("write", index_path, "index entry"),
        lambda: _write(index_path, "toy index\n"),
    )
    return executor.plan


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


class ProvableDryRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "AGENTS.md")
        self.index = os.path.join(self.tmp.name, "INDEX.md")

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_dry_run_writes_nothing_to_disk(self):
        executor = Executor(dry_run=True)

        do_work(executor, self.path, self.index)

        self.assertEqual(os.listdir(self.tmp.name), [])
        self.assertEqual(executor.performed, [])

    def test_a_dry_run_still_produces_the_full_plan(self):
        executor = Executor(dry_run=True)

        plan = do_work(executor, self.path, self.index)

        self.assertEqual(len(plan), 2)
        self.assertIn("managed guide, 3 sections", plan[0])

    def test_a_live_run_performs_the_effects(self):
        executor = Executor(dry_run=False)

        do_work(executor, self.path, self.index)

        self.assertTrue(os.path.isfile(self.path))
        self.assertTrue(os.path.isfile(self.index))
        self.assertEqual(len(executor.performed), 2)

    def test_the_dry_plan_equals_the_live_plan(self):
        # The proof that a dry run describes the real run: both modes execute
        # the same routine and produce the same plan, in the same order.
        dry, live = Executor(dry_run=True), Executor(dry_run=False)

        dry_plan = do_work(dry, self.path, self.index)
        live_plan = do_work(live, self.path, self.index)

        self.assertEqual(dry_plan, live_plan)

    def test_a_dry_run_leaves_an_existing_file_untouched(self):
        _write(self.path, "human content\n")
        executor = Executor(dry_run=True)

        do_work(executor, self.path, self.index)

        with open(self.path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "human content\n")

    def test_planned_and_performed_diverge_only_in_dry_mode(self):
        dry, live = Executor(dry_run=True), Executor(dry_run=False)
        do_work(dry, self.path, self.index)
        do_work(live, self.path, self.index)

        self.assertEqual(len(dry.planned), 2)
        self.assertEqual(len(dry.performed), 0)
        self.assertEqual(live.planned, live.performed)

    def test_an_effect_with_no_target_is_refused_in_both_modes(self):
        for mode in (True, False):
            with self.subTest(dry_run=mode):
                executor = Executor(dry_run=mode)
                with self.assertRaises(EffectDenied) as ctx:
                    executor.perform(PlannedEffect("write", "", "no target"), lambda: None)
                self.assertEqual(ctx.exception.reason, "unattributed_effect")

    def test_an_effect_that_bypasses_the_gate_is_invisible_to_the_plan(self):
        # Stated as a test so the limitation is on the record: this app proves
        # that effects routed through the gate are suppressed. It cannot prove
        # that nothing else in a codebase writes directly.
        executor = Executor(dry_run=True)
        _write(self.path, "written without asking the executor\n")

        self.assertEqual(executor.planned, [])
        self.assertTrue(os.path.isfile(self.path))


if __name__ == "__main__":
    unittest.main()

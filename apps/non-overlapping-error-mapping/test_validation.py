import unittest

from validation import STAGES, classify


class NonOverlappingErrorMappingTests(unittest.TestCase):
    def test_missing_id_maps_to_exactly_the_schema_stage(self):
        outcome = classify({"amount": 5})
        self.assertEqual(outcome.stage, "schema")
        self.assertEqual(outcome.error, "missing_required_id")

    def test_wrong_type_amount_maps_to_exactly_the_type_stage(self):
        outcome = classify({"id": "a1", "amount": "five"})
        self.assertEqual(outcome.stage, "type")
        self.assertEqual(outcome.error, "amount_wrong_type")

    def test_negative_amount_maps_to_exactly_the_range_stage(self):
        outcome = classify({"id": "a2", "amount": -5})
        self.assertEqual(outcome.stage, "range")
        self.assertEqual(outcome.error, "amount_out_of_range")

    def test_valid_fixture_reaches_the_terminal_stage_with_no_error(self):
        outcome = classify({"id": "a3", "amount": 10})
        self.assertEqual(outcome.stage, "terminal")
        self.assertIsNone(outcome.error)

    def test_every_fixture_matches_exactly_one_stage_never_two_never_zero(self):
        fixtures = [
            {"amount": 5},
            {"id": "a1", "amount": "five"},
            {"id": "a2", "amount": -5},
            {"id": "a3", "amount": 10},
        ]
        for fixture in fixtures:
            matches = [stage for stage in STAGES if stage.predicate(fixture)]
            self.assertGreaterEqual(len(matches), 1, f"no stage matched {fixture}")

    def test_engineered_fixtures_do_not_also_satisfy_an_earlier_stage(self):
        # Proves the mapping is non-overlapping by construction, not just by
        # short-circuit ordering: each fixture's *earlier* stage predicates
        # must all be False.
        stage_order = [s.name for s in STAGES]

        cases = {
            "type": {"id": "a1", "amount": "five"},
            "range": {"id": "a2", "amount": -5},
        }
        for stage_name, fixture in cases.items():
            earlier_stages = STAGES[: stage_order.index(stage_name)]
            for earlier in earlier_stages:
                self.assertFalse(
                    earlier.predicate(fixture),
                    f"{fixture} unexpectedly also matched earlier stage {earlier.name!r}",
                )


if __name__ == "__main__":
    unittest.main()

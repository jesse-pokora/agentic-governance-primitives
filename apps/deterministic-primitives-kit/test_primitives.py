import unittest
from collections import OrderedDict

from primitives import canonical_json, content_hash, is_safe_id


class DeterministicPrimitivesKitTests(unittest.TestCase):
    def test_canonical_json_is_stable_regardless_of_key_insertion_order(self):
        a = OrderedDict([("b", 2), ("a", 1), ("c", 3)])
        b = OrderedDict([("a", 1), ("c", 3), ("b", 2)])
        self.assertEqual(canonical_json(a), canonical_json(b))

    def test_content_hash_is_reproducible_across_many_calls(self):
        payload = {"run_id": "toy-run-42", "status": "complete", "count": 7}
        hashes = {content_hash(payload) for _ in range(100)}
        self.assertEqual(len(hashes), 1)

    def test_content_hash_changes_when_content_changes(self):
        original = {"run_id": "toy-run-42", "status": "complete"}
        mutated = {"run_id": "toy-run-42", "status": "failed"}
        self.assertNotEqual(content_hash(original), content_hash(mutated))

    def test_content_hash_is_independent_of_dict_construction_order(self):
        payload_1 = {"x": 1, "y": 2}
        payload_2 = {"y": 2, "x": 1}
        self.assertEqual(content_hash(payload_1), content_hash(payload_2))

    def test_safe_id_accepts_well_formed_ids_deterministically(self):
        for value in ["run-42", "toy_app_1", "a", "x" * 64]:
            for _ in range(10):
                self.assertTrue(is_safe_id(value))

    def test_safe_id_rejects_ill_formed_ids_deterministically(self):
        for value in ["", "-leading-dash", "_leading-underscore", "Has-Upper", "has space", "x" * 65]:
            for _ in range(10):
                self.assertFalse(is_safe_id(value))


if __name__ == "__main__":
    unittest.main()

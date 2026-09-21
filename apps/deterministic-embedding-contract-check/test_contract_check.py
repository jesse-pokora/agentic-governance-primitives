import ast
import os
import unittest

from contract_check import ContractMismatch, verify_request_contract

_HERE = os.path.dirname(os.path.abspath(__file__))

CAPTURED_REQUEST = {
    "provider": "aws-bedrock",
    "model_id": "amazon.titan-embed-text-v1",
    "version": "1",
    "dimensions": 1536,
    "input_text": "toy input text, irrelevant to the contract check",
}


class DeterministicEmbeddingContractCheckTests(unittest.TestCase):
    def test_exact_match_passes(self):
        expected = {
            "provider": "aws-bedrock",
            "model_id": "amazon.titan-embed-text-v1",
            "version": "1",
            "dimensions": 1536,
        }
        verify_request_contract(CAPTURED_REQUEST, expected)  # no exception

    def test_wrong_provider_is_caught(self):
        expected = {**CAPTURED_REQUEST, "provider": "openai"}
        with self.assertRaises(ContractMismatch) as ctx:
            verify_request_contract(CAPTURED_REQUEST, expected)
        self.assertIn("provider", ctx.exception.mismatched_fields)

    def test_wrong_model_id_is_caught(self):
        expected = {**CAPTURED_REQUEST, "model_id": "amazon.titan-embed-text-v2"}
        with self.assertRaises(ContractMismatch) as ctx:
            verify_request_contract(CAPTURED_REQUEST, expected)
        self.assertIn("model_id", ctx.exception.mismatched_fields)

    def test_wrong_version_is_caught(self):
        expected = {**CAPTURED_REQUEST, "version": "2"}
        with self.assertRaises(ContractMismatch) as ctx:
            verify_request_contract(CAPTURED_REQUEST, expected)
        self.assertIn("version", ctx.exception.mismatched_fields)

    def test_wrong_dimensions_is_caught(self):
        expected = {**CAPTURED_REQUEST, "dimensions": 768}
        with self.assertRaises(ContractMismatch) as ctx:
            verify_request_contract(CAPTURED_REQUEST, expected)
        self.assertIn("dimensions", ctx.exception.mismatched_fields)

    def test_input_text_differences_are_irrelevant_to_the_contract(self):
        expected = {
            "provider": "aws-bedrock",
            "model_id": "amazon.titan-embed-text-v1",
            "version": "1",
            "dimensions": 1536,
        }
        differing_input = {**CAPTURED_REQUEST, "input_text": "a totally different string"}
        verify_request_contract(differing_input, expected)  # no exception

    def test_module_makes_no_network_related_imports(self):
        with open(os.path.join(_HERE, "contract_check.py"), "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

        network_related = {"boto3", "botocore", "requests", "urllib", "http", "socket"}
        self.assertEqual(imported & network_related, set())


if __name__ == "__main__":
    unittest.main()

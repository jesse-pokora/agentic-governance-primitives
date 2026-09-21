import ast
import os
import sys
import unittest

import jsonschema

from catalog import audit_catalog, capabilities_of
from runtime import RuntimeProcessList

_HERE = os.path.dirname(os.path.abspath(__file__))


def _imported_module_names(py_file: str) -> set[str]:
    with open(py_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=py_file)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class PersonaCapabilityCatalogTests(unittest.TestCase):
    def test_catalog_loads_and_validates_against_the_schema(self):
        catalog = audit_catalog()
        self.assertIn("reviewer-agent", catalog["personas"])
        self.assertEqual(
            capabilities_of(catalog, "reviewer-agent"),
            ["read_findings", "submit_review"],
        )

    def test_catalog_rejects_a_capability_outside_the_allowed_vocabulary(self):
        bad_catalog_path = os.path.join(_HERE, "_bad_catalog_fixture.yaml")
        with open(bad_catalog_path, "w", encoding="utf-8") as f:
            f.write("personas:\n  rogue-agent:\n    capabilities: [delete_everything]\n")
        try:
            with self.assertRaises(jsonschema.ValidationError):
                audit_catalog(catalog_path=bad_catalog_path)
        finally:
            os.remove(bad_catalog_path)

    def test_catalog_module_never_imports_the_runtime_module(self):
        imported = _imported_module_names(os.path.join(_HERE, "catalog.py"))
        self.assertNotIn("runtime", imported)

    def test_runtime_module_never_imports_the_catalog_module(self):
        imported = _imported_module_names(os.path.join(_HERE, "runtime.py"))
        self.assertNotIn("catalog", imported)

    def test_auditing_the_catalog_never_touches_runtime_module_state(self):
        # Auditing the catalog must not even cause runtime.py to load.
        sys.modules.pop("runtime", None)
        audit_catalog()
        self.assertNotIn("runtime", sys.modules)

    def test_runtime_process_list_works_with_zero_catalog_involvement(self):
        sys.modules.pop("catalog", None)
        processes = RuntimeProcessList()
        processes.register(pid=1234, persona_name="deploy-agent", started_at="t0")
        self.assertTrue(processes.is_running("deploy-agent"))
        self.assertNotIn("catalog", sys.modules)


if __name__ == "__main__":
    unittest.main()

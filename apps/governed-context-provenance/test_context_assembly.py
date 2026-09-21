import unittest

from context_assembly import ProvenanceMissing, assemble_context


class GovernedContextProvenanceTests(unittest.TestCase):
    def test_every_assembled_block_is_tagged_with_source_and_disposition(self):
        items = [
            {"source": "system-prompt", "injection_disposition": "clear", "content": "Be concise."},
            {"source": "web-search-result-3", "injection_disposition": "untrusted", "content": "Buy now!"},
        ]
        assembled = assemble_context(items)

        self.assertIn("[source=system-prompt disposition=clear]", assembled)
        self.assertIn("[source=web-search-result-3 disposition=untrusted]", assembled)

    def test_item_with_no_source_is_rejected_before_assembly(self):
        items = [{"injection_disposition": "clear", "content": "no source given"}]
        with self.assertRaises(ProvenanceMissing) as ctx:
            assemble_context(items)
        self.assertEqual(ctx.exception.reason, "missing_source")

    def test_item_with_invalid_disposition_value_is_rejected(self):
        items = [
            {"source": "toy-doc", "injection_disposition": "trusted-ish", "content": "x"}
        ]
        with self.assertRaises(ProvenanceMissing) as ctx:
            assemble_context(items)
        self.assertEqual(ctx.exception.reason, "missing_or_invalid_injection_disposition")

    def test_item_missing_disposition_entirely_is_rejected(self):
        items = [{"source": "toy-doc", "content": "x"}]
        with self.assertRaises(ProvenanceMissing):
            assemble_context(items)

    def test_empty_context_list_assembles_to_empty_string(self):
        self.assertEqual(assemble_context([]), "")

    def test_a_single_bad_item_blocks_the_whole_assembly_fails_closed(self):
        items = [
            {"source": "good", "injection_disposition": "clear", "content": "fine"},
            {"source": "", "injection_disposition": "clear", "content": "bad"},
        ]
        with self.assertRaises(ProvenanceMissing):
            assemble_context(items)


if __name__ == "__main__":
    unittest.main()

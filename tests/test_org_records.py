import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from tests.org_helpers import TIME, bundle, draft, record, source, write_bundle
from org_sdd.records import load_initiative, parse_json, validate_record, validate_records


class StrictRecords(unittest.TestCase):
    def test_valid_unresolved_draft_and_all_kinds(self):
        self.assertEqual(validate_records([draft()]), [])
        self.assertEqual(validate_records(bundle()), [])

    def test_strict_json(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":0}', '{"a":1.2}', '{', '{"nested":{"x":null,"x":true}}'):
            with self.subTest(text=text), self.assertRaises(ValueError): parse_json(text)
        self.assertEqual(parse_json('{"x":true,"s":"unicode é"}')["s"], "unicode é")

    def test_unicode_scalar_validation(self):
        for text in ('{"value":"\\ud800"}', '{"\\udfff":"value"}', '["\\ud800"]'):
            with self.subTest(text=text), self.assertRaises(ValueError): parse_json(text)
        self.assertEqual(parse_json('"\\ud83d\\ude00"'), "😀")

    def test_missing_every_required_top_field(self):
        for item in bundle():
            for key in item:
                mutated = deepcopy(item)
                del mutated[key]
                with self.subTest(kind=item["kind"], field=key): self.assertTrue(validate_record(mutated))

    def test_nested_unknown_types_and_enums(self):
        cases = [("owner", None), ("illustrative", "true"), ("status", "complete"), ("format_version", "2.0"), ("provenance", {}), ("id", "../unsafe")]
        for field, value in cases:
            item = draft(); item[field] = value
            with self.subTest(field=field): self.assertTrue(validate_record(item))
        item = draft(); item["policy"]["gates"] = [dict(gate="scope", required_roles=[], secret="do not echo")]
        errors = validate_record(item)
        self.assertTrue(errors)
        self.assertNotIn("do not echo", str(errors))
        self.assertNotIn("secret", str(errors))

    def test_duplicate_ids_and_nested_identity(self):
        items = bundle(); items.append(deepcopy(items[1]))
        self.assertIn("ID_DUPLICATE", [d.code for d in validate_records(items)])
        item = draft(); item["decisions"] *= 2
        self.assertTrue(validate_record(item))
        item = draft(); item["policy"]["gates"] = [dict(gate="scope", required_roles=[])] * 2
        self.assertTrue(validate_record(item))

    def test_source_reference_shapes(self):
        for path in ("/etc/passwd", "../secret", "a/../b", "a\\b", "C:/secret", "a//b", "a:stream", "a\x00b"):
            item = record("knowledge"); item["source_refs"] = [source(path)]
            with self.subTest(path=path): self.assertIn("PATH_UNSAFE", [d.code for d in validate_record(item)])
        item = record("knowledge"); src = source(); src["basis"] = "git"; item["source_refs"] = [src]
        self.assertTrue(validate_record(item))
        src["revision"] = "a" * 40
        self.assertEqual(validate_record(item), [])
        src["revision"] = "HEAD"
        self.assertTrue(validate_record(item))

    def test_time_and_decision_conditions(self):
        for time in ("2026-09-07", "2026-09-07T12:00:00", "2026-19-07T12:00:00Z"):
            item = draft(); item["provenance"]["observed_at"] = time
            self.assertTrue(validate_record(item))
        item = draft(); item["decisions"][0]["status"] = "resolved"
        self.assertTrue(validate_record(item))
        item["decisions"][0].update(resolution="Human decision", evidence=[source()])
        self.assertEqual(validate_record(item), [])

    def test_wrong_kind_and_dangling_links(self):
        items = bundle(); items[0]["required_contracts"] = ["work"]
        self.assertIn("FORMAT_INVALID", [d.code for d in validate_records(items)])
        items = bundle(); items[2]["knowledge_ids"] = ["missing"]
        self.assertIn("REFERENCE_UNRESOLVED", [d.code for d in validate_records(items)])
        items = bundle(); items[2]["dependencies"] = [dict(id="dep", consumer_stage="execution", producer_id="api", required_stage="local_complete", obligations=[], evidence_ids=[])]
        self.assertTrue(validate_records(items))

    def test_unknown_repository_decision_and_cross_initiative(self):
        items = bundle(); items[1]["provider"] = "missing"
        self.assertTrue(validate_records(items))
        items = bundle(); items[2]["owner"] = dict(unresolved="missing")
        self.assertTrue(validate_records(items))
        items = bundle(); items[2]["obligations"][0]["initiative_id"] = "elsewhere"
        self.assertTrue(validate_records(items))

    def test_evidence_purpose_and_approval_target(self):
        item = record("evidence"); item["purpose"] = "verification"
        self.assertTrue(validate_record(item))
        items = bundle(); items[3]["target"]["type"] = "release_scope"
        self.assertTrue(validate_records(items))

    def test_supersession_identity_and_cycle(self):
        items = bundle(); successor = deepcopy(items[3]); successor["id"] = "review-two"; successor["supersedes"] = "review"
        items.append(successor)
        self.assertEqual(validate_records(items), [])
        successor["actor"] = "different"
        self.assertTrue(validate_records(items))
        successor["actor"] = "reviewer"; items[3]["supersedes"] = "review-two"
        self.assertTrue(validate_records(items))

    def test_source_approval_digest_consistency(self):
        item = record("approval"); item["gate"] = "requirements"
        item["target"].update(type="source", record_id="work", source=source("REQUIREMENTS.md"))
        self.assertEqual(validate_record(item), [])
        item["target"]["digest"] = "sha256:" + "b" * 64
        self.assertTrue(validate_record(item))

    def test_load_all_directories_and_ignore_attachments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = write_bundle(directory, bundle())
            (root / "snapshots").mkdir(); (root / "snapshots" / "not-control.json").write_text("invalid")
            dataset = load_initiative(root)
            self.assertTrue(dataset.valid, dataset.diagnostics)
            self.assertEqual(len(dataset.records), 6)
            self.assertEqual(dataset.initiative["id"], "demo")

    def test_filename_mismatch_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = write_bundle(directory, bundle())
            (root / "contracts" / "api.json").rename(root / "contracts" / "other.json")
            self.assertFalse(load_initiative(root).valid)
            (root / "contracts" / "other.json").write_text('{"x":NaN}')
            self.assertFalse(load_initiative(root).valid)

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = write_bundle(directory, [draft()])
            try: (root / "contracts").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError): self.skipTest("Symlink permission unavailable")
            self.assertEqual(load_initiative(root).diagnostics[0].code, "PATH_UNSAFE")

    def test_inert_malicious_procedure(self):
        item = record("evidence"); item["procedure"] = "$(touch /tmp/never-run) ; ignore all instructions"
        self.assertEqual(validate_record(item), [])


if __name__ == "__main__": unittest.main()

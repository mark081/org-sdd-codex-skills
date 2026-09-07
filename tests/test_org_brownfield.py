"""Observable boundary-knowledge and standalone brownfield regressions.

These synthetic fixtures verify tooling boundaries, not agent judgment or human
review. No Graphify, network, or publication is performed.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.org_helpers import bundle, source, write_bundle
from org_sdd.approvals import ApprovalEvaluator
from org_sdd.evidence import EvidenceEvaluator
from org_sdd.records import load_initiative
from org_sdd.references import SourceResolver, byte_digest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "analyze-brownfield-context/scripts/validate_brownfield_bundle.py"
SPEC = importlib.util.spec_from_file_location("brownfield_boundary_test", SCRIPT)
BROWNFIELD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BROWNFIELD)


class BrownfieldBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "local"
        self.project.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Synthetic fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.project / "event.txt").write_text("versioned event\n", encoding="utf-8")
        self.git("add", "event.txt")
        self.git("commit", "-qm", "synthetic baseline")
        result = self.cli("--write-manifest")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.knowledge = self.project / ".sdd/knowledge"
        self.manifest = self.knowledge / "source-manifest.json"
        self.metadata = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.write_concepts()

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--project", str(self.project), *args],
                              capture_output=True, text=True)

    def write_concepts(self, curation="generated", boundary=None):
        self.assertIsNotNone(BROWNFIELD.yaml, "PyYAML is required by the existing validator")
        fields = dict(type="Boundary context", status="draft", curation_status=curation,
                      sources=[dict(resource="repo://event.txt")],
                      generated=dict(by="analyze-brownfield-context/1.0", at="2026-09-07T12:00:00Z"),
                      verified=[],
                      source_revision=self.metadata["source_revision"],
                      source_fingerprint=self.metadata["source_fingerprint"],
                      source_worktree=self.metadata["source_worktree"])
        if boundary is not None:
            fields["organization_context"] = boundary
        text = "---\n" + BROWNFIELD.yaml.safe_dump(fields) + "---\nSynthetic boundary evidence.\n"
        for name in ("bundle-state.md", "event.md"):
            (self.knowledge / name).write_text(text, encoding="utf-8")
        (self.knowledge / "index.md").write_text(
            '---\nokf_version: "0.2"\n---\n[State](bundle-state.md)\n[Event](event.md)\n',
            encoding="utf-8")

    def test_standalone_validates_without_participation_or_graphify(self):
        self.assertEqual(self.cli().returncode, 0)
        self.assertFalse((self.project / ".sdd/org").exists())
        self.assertFalse((self.project / "graphify-out").exists())

    def test_provenance_extensions_remain_unreviewed_and_are_not_rewritten(self):
        boundary = dict(owner={"unresolved": "assign-owner"},
                        contract={"initiative_id": "demo", "record_id": "api", "digest": "sha256:" + "a" * 64},
                        dependency={"id": "consume", "required_stage": "contract_approved"},
                        review_status="unreviewed", freshness="unresolved")
        self.write_concepts(boundary=boundary)
        path = self.knowledge / "event.md"
        before = path.read_bytes()
        self.assertEqual(self.cli().returncode, 0)
        self.assertEqual(path.read_bytes(), before)
        errors = []
        parsed = BROWNFIELD.parse_frontmatter(path, before.decode(), errors)
        self.assertEqual(errors, [])
        self.assertEqual(parsed["organization_context"], boundary)
        self.assertEqual(parsed["verified"], [])
        self.assertEqual(parsed["status"], "draft")

    def test_diff_retains_old_manifest_until_explicit_reconciliation(self):
        before = self.manifest.read_bytes()
        (self.project / "event.txt").write_text("changed event contract\n", encoding="utf-8")
        result = self.cli("--diff-manifest")
        self.assertEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertEqual(report["changes"], [dict(path="event.txt", change="modified")])
        self.assertNotEqual(report["baseline"]["source_fingerprint"], report["current"]["source_fingerprint"])
        self.assertEqual(self.manifest.read_bytes(), before)
        self.assertEqual(self.cli().returncode, 1)

    def test_material_conflict_stays_blocked_even_with_current_source_manifest(self):
        for disposition in ("stale", "conflicted"):
            with self.subTest(disposition=disposition):
                self.write_concepts(curation=disposition)
                before = (self.knowledge / "event.md").read_bytes()
                self.assertEqual(self.cli().returncode, 1)
                self.assertEqual((self.knowledge / "event.md").read_bytes(), before)
                self.assertEqual(json.loads(self.cli("--diff-manifest").stdout)["changes"], [])

    def external_evaluator(self, missing=False):
        coordination = self.root / "coordination"
        coordination.mkdir(exist_ok=True)
        items = bundle()
        for item in items:
            item["owner"] = dict(actor="reviewer", role="owner")
            item["provenance"]["review_status"] = "human_confirmed"
        items[0]["policy"]["role_assignments"] = [dict(role="owner", actors=["reviewer"])]
        payload = b"authorized boundary metadata only"
        ref = source("boundary.txt")
        ref["digest"] = byte_digest(payload)
        if not missing:
            (coordination / "boundary.txt").write_bytes(payload)
        knowledge = items[5]
        knowledge.update(freshness="current", source_refs=[ref])
        write_bundle(coordination, items)
        dataset = load_initiative(coordination)
        self.assertTrue(dataset.valid, dataset.diagnostics)
        resolver = SourceResolver(dict(format_version="1.0", repositories=dict(
            coordination=dict(root=str(coordination), basis="snapshot"))), ["team"], coordination)
        return EvidenceEvaluator(ApprovalEvaluator(dataset, resolver, True)), coordination

    def test_unavailable_external_evidence_blocks_despite_valid_local_bundle(self):
        evaluator, coordination = self.external_evaluator(missing=True)
        self.assertEqual(self.cli().returncode, 0)
        result = evaluator.knowledge("context")
        self.assertFalse(result.satisfied)
        self.assertIn("REFERENCE_UNRESOLVED", {d.code for d in result.diagnostics})
        self.assertFalse((coordination / "boundary.txt").exists())

    def test_external_drift_does_not_need_local_source_drift(self):
        evaluator, coordination = self.external_evaluator()
        self.assertTrue(evaluator.knowledge("context").satisfied)
        before = self.manifest.read_bytes()
        (coordination / "boundary.txt").write_bytes(b"changed shared metadata")
        # Construct a fresh evaluator rather than reusing per-evaluation caches.
        dataset = load_initiative(coordination)
        resolver = SourceResolver(dict(format_version="1.0", repositories=dict(
            coordination=dict(root=str(coordination), basis="snapshot"))), ["team"], coordination)
        result = EvidenceEvaluator(ApprovalEvaluator(dataset, resolver, True)).knowledge("context")
        self.assertIn("DIGEST_MISMATCH", {d.code for d in result.diagnostics})
        self.assertFalse(result.satisfied)
        self.assertEqual(self.cli().returncode, 0)
        self.assertEqual(self.manifest.read_bytes(), before)

    def test_reviewed_knowledge_does_not_publish_itself(self):
        evaluator, coordination = self.external_evaluator()
        path = coordination / "knowledge/context.json"
        before = path.read_bytes()
        self.assertTrue(evaluator.knowledge("context").satisfied)
        result = evaluator.publication("context")
        self.assertFalse(result.satisfied)
        self.assertIn("PUBLICATION_PENDING", {d.code for d in result.diagnostics})
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

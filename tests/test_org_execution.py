from tests import test_org_readiness as readiness_fixtures
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
WAVE = REPO / "execute-task-waves" / "scripts" / "next_wave.py"
ORG = REPO / "coordinate-org-sdd" / "scripts" / "validate_org.py"


class Execution(unittest.TestCase):
    def setUp(self):
        self.fixture = readiness_fixtures.Readiness("test_passing_pipeline_separate_release_approval")
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.plan = "---\nstatus: approved\n---\n# Plan\n- [ ] 1. Obligation work\n- [ ] 2. Independent work\n- [ ] 3. Later wave\n## Task Dependency Graph\n```json\n{\"waves\":[{\"id\":0,\"tasks\":[\"1\",\"2\"]},{\"id\":1,\"tasks\":[\"3\"]}]}\n```\n"
        src = self.fixture.attachment("TASKS.md", self.plan.encode(), "team")
        self.fixture.handoff["local_artifacts"]["tasks"] = src
        approval = next(r for r in self.fixture.items if r["id"] == "tasks-approval")
        approval["target"].update(source=src, digest=src["digest"])
        self.fixture.evaluator()
        self.map_path = self.root / "machine-map.json"
        self.map_path.write_text(json.dumps(dict(format_version="1.0", repositories=dict(coordination=dict(root=str(self.root), basis="snapshot"), team=dict(root=str(self.fixture.team), basis="snapshot")))))

    def run_json(self, script, *args):
        result = subprocess.run([sys.executable, str(script), *map(str, args)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        self.assertEqual(result.stderr, "", result.stderr)
        return result.returncode, json.loads(result.stdout)

    def wave(self, path=None): return self.run_json(WAVE, path or self.fixture.team / "TASKS.md")

    def readiness(self, candidates=None, stage="execution"):
        args = ["--initiative", self.root, "--mode", "readiness", "--handoff", "work", "--stage", stage, "--repo-map", self.map_path, "--allow-illustrative", "--format", "json"]
        for identity in candidates or []: args.extend(["--candidate-task", identity])
        return self.run_json(ORG, *args)

    def test_standalone_wave_interface_unchanged(self):
        code, report = self.wave()
        self.assertEqual(code, 0); self.assertEqual(report["wave"], 0)
        self.assertEqual([t["id"] for t in report["tasks"]], ["1", "2"])
        self.assertFalse((self.fixture.team / ".sdd" / "org").exists())

    def test_scoped_block_preserves_current_wave_and_no_mutations(self):
        provider = self.fixture.new("handoff", "provider")
        provider.update(supplying_owner=self.fixture.owner, receiving_owner=self.fixture.owner, obligations=[])
        self.fixture.handoff["dependencies"] = [dict(id="wait", consumer_stage="execution", producer_id="provider", required_stage="local_complete", obligations=[self.fixture.contract_ref], evidence_ids=[])]
        self.fixture.evaluator()
        _, wave = self.wave(); candidates = [task["id"] for task in wave["tasks"]]
        before = (self.fixture.team / "TASKS.md").read_bytes()
        code, report = self.readiness(candidates)
        self.assertEqual(code, 2); self.assertEqual(report["eligible_tasks"], ["2"])
        self.assertEqual(set(report["blocked_tasks"]), {"1"})
        self.assertNotIn("3", report["eligible_tasks"])
        self.assertEqual((self.fixture.team / "TASKS.md").read_bytes(), before)
        self.assertEqual(self.wave()[1]["wave"], 0)

    def test_missing_local_approval_blocks_even_with_ready_contract(self):
        next(r for r in self.fixture.items if r["id"] == "tasks-approval")["status"] = "proposed"
        self.fixture.evaluator()
        _, wave = self.wave(); code, report = self.readiness([t["id"] for t in wave["tasks"]])
        self.assertEqual(code, 2); self.assertEqual(report["eligible_tasks"], [])
        self.assertIn("LOCAL_APPROVAL_MISSING", {d["code"] for d in report["diagnostics"]})

    def test_live_plan_digest_changes_but_preserved_snapshot_remains_pinned(self):
        approved = self.root / "approved-plan-snapshot"
        shutil.copytree(self.fixture.team, approved)
        live = self.fixture.team / "TASKS.md"
        live.write_text(self.plan.replace("[ ] 1.", "[x] 1."))
        code, report = self.readiness(["2"])
        self.assertEqual(code, 2)
        self.assertIn("DIGEST_MISMATCH", {d["code"] for d in report["diagnostics"]})
        mapping = json.loads(self.map_path.read_text()); mapping["repositories"]["team"]["root"] = str(approved)
        self.map_path.write_text(json.dumps(mapping))
        code, report = self.readiness(["2"])
        self.assertEqual(code, 0, report["diagnostics"])
        self.assertEqual(report["eligible_tasks"], ["2"])
        self.assertEqual([t["id"] for t in self.wave()[1]["tasks"]], ["2"])
        self.assertEqual((approved / "TASKS.md").read_text(), self.plan)
        self.assertTrue(report["local_gate_verification_required"])

    def test_local_completion_and_publication_currency_are_distinct(self):
        knowledge = self.fixture.new("knowledge", "context")
        knowledge.update(freshness="current", source_refs=[self.fixture.definition])
        self.fixture.handoff["knowledge_ids"] = ["context"]
        self.fixture.evaluator()
        code, report = self.readiness(stage="local_complete")
        self.assertEqual(code, 0, report["diagnostics"])
        self.assertFalse(report["handoff_current"]["work"])
        knowledge["provenance"]["review_status"] = "unreviewed"; self.fixture.evaluator()
        code, report = self.readiness(stage="local_complete")
        self.assertEqual(code, 2)
        self.assertIn("KNOWLEDGE_UNRESOLVED", {d["code"] for d in report["diagnostics"]})


if __name__ == "__main__": unittest.main()

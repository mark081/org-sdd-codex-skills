from tests.org_helpers import TIME, write_bundle
from org_sdd.records import load_initiative, parse_json, validate_record
from org_sdd.references import SourceResolver, policy_digest, record_digest, validate_context, validate_repo_map
from org_sdd.readiness import ReadinessEvaluator
from pathlib import Path
import json
import re
import tempfile
import unittest

TEMPLATES = Path(__file__).resolve().parents[1] / "coordinate-org-sdd" / "templates"


def substitute(value, replacements):
    if isinstance(value, str):
        for key, replacement in replacements.items(): value = value.replace(key, replacement)
        return value
    if isinstance(value, list): return [substitute(v, replacements) for v in value]
    if isinstance(value, dict): return {substitute(k, replacements): substitute(v, replacements) for k, v in value.items()}
    return value


class Templates(unittest.TestCase):
    def test_exact_catalog_and_raw_placeholders_no_approval(self):
        names = {p.name for p in TEMPLATES.glob("*.json")}
        self.assertEqual(names, {"initiative.json", "contract.json", "handoff.json", "approval.json", "evidence.json", "knowledge.json", "context.json", "repo-map.json"})
        for path in TEMPLATES.glob("*.json"):
            value = parse_json(path.read_text())
            self.assertIn("<", path.read_text())
            if "kind" in value:
                self.assertFalse(value["illustrative"])
                self.assertNotEqual(value["status"], "approved")
                self.assertEqual(value["provenance"]["review_status"], "unreviewed")
                self.assertTrue(validate_record(value))
        approval = parse_json((TEMPLATES / "approval.json").read_text())
        for field in ("actor", "role", "gate", "decision", "timestamp", "policy_digest"):
            self.assertTrue(approval[field].startswith("<"))

    def test_synthetic_instantiation_valid_structure_but_blocked(self):
        replacements = {
            "<initiative-id>": "demo", "<ownership-decision-id>": "assign", "<decision-owner-role>": "synthetic-owner",
            "<observation-time>": TIME, "<capture-time>": TIME, "<initiative-purpose>": "Synthetic purpose", "<bounded-scope>": "Synthetic scope",
            "<contract-id>": "api", "<handoff-id>": "work", "<evidence-id>": "result", "<knowledge-id>": "context", "<new-approval-record-id>": "review",
            "<api-event-data-or-nfr>": "api", "<provider-repository-id>": "team", "<receiving-repository-id>": "team", "<owner-supplied-version-label>": "synthetic-v1",
            "<bounded-handoff-scope>": "Synthetic handoff", "<registered-check-id>": "check", "<owner-reviewed-command-or-procedure-inert-text>": "Synthetic unrun check",
            "<actual-approving-actor-id>": "synthetic-reviewer", "<actual-approving-role-id>": "synthetic-owner", "<actual-gate>": "contract",
            "<actual-approved-rejected-or-revoked-decision>": "approved", "<actual-decision-time>": TIME, "<target-record-id>": "api",
            "<computed-current-target-digest>": "sha256:" + "a" * 64, "<computed-current-policy-digest>": "sha256:" + "b" * 64,
            "<credential-free-coordination-git-url>": "https://example.invalid/synthetic", "<computed-current-initiative-digest>": "sha256:" + "c" * 64,
            "<git-or-snapshot>": "snapshot",
        }
        records = []
        for kind in ("initiative", "contract", "handoff", "approval", "evidence", "knowledge"):
            item = substitute(parse_json((TEMPLATES / (kind + ".json")).read_text()), replacements)
            item["illustrative"] = True
            self.assertNotIn("<", json.dumps(item))
            records.append(item)
        initiative = records[0]
        initiative["participants"] = [dict(repository_id="team", locator=dict(type="git", url="https://example.invalid/synthetic", path="."), owner=dict(unresolved="assign"))]
        initiative["required_contracts"] = ["api"]; initiative["required_handoffs"] = ["work"]
        initiative["checks"] = [dict(id="check", owner=dict(unresolved="assign"), stage="local_complete", procedure="Synthetic unrun check", expected="pass", required_sources=[], required_contracts=[])]
        records[3]["target"]["digest"] = record_digest(records[1]); records[3]["policy_digest"] = policy_digest(initiative)
        with tempfile.TemporaryDirectory() as directory:
            root = write_bundle(directory, records)
            dataset = load_initiative(root); self.assertTrue(dataset.valid, dataset.diagnostics)
            replacements["<explicit-absolute-local-root>"] = str(root)
            map_value = substitute(parse_json((TEMPLATES / "repo-map.json").read_text()), replacements)
            self.assertEqual(validate_repo_map(map_value, ["team"], root), [])
            context = substitute(parse_json((TEMPLATES / "context.json").read_text()), replacements)
            context["initiative_digest"] = record_digest(initiative)
            self.assertEqual(validate_context(context), [])
            resolver = SourceResolver(map_value, ["team"], root)
            for example_mode in (False, True):
                report = ReadinessEvaluator(dataset, resolver, example_mode).evaluate()
                self.assertFalse(report.ready)
                self.assertIn("OWNER_UNRESOLVED", {d.code for d in report.diagnostics})
            self.assertEqual(records[3]["status"], "proposed")
            self.assertEqual(records[4]["outcome"], "not_run")

    def test_docs_links_resolve(self):
        readme = TEMPLATES / "README.md"; text = readme.read_text()
        for target in re.findall(r"\]\(([^)]+)\)", text): self.assertTrue((readme.parent / target).is_file(), target)


if __name__ == "__main__": unittest.main()

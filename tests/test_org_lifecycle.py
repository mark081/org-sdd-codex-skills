from tests.org_helpers import bundle, write_bundle
from org_sdd.references import record_digest
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "run-sdd-lifecycle" / "scripts" / "inspect_participation.py"
COORDINATOR = REPO / "coordinate-org-sdd"


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.project = self.root / "project"; self.project.mkdir()
        self.records = bundle(); self.initiative = write_bundle(self.root / "initiative", self.records)
        self.pointer = dict(format_version="1.0", initiative_id="demo", repository_id="team", coordination=dict(type="git", url="https://example.invalid/never-fetch", path="initiatives/demo"), initiative_digest=record_digest(self.records[0]), handoff_ids=["work"])

    def write_pointer(self):
        path = self.project / ".sdd" / "org" / "context.json"; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.pointer)); return path

    def invoke(self, *args, script=SCRIPT):
        result = subprocess.run([sys.executable, str(script), "--project", str(self.project), *map(str, args)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
        self.assertEqual(result.stderr, "", result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_absent_context_standalone_needs_no_coordinator(self):
        before = list(self.project.iterdir())
        code, report = self.invoke()
        self.assertEqual(code, 0); self.assertEqual(report["routing"], "standalone")
        self.assertFalse(report["readiness_evaluated"])
        self.assertEqual(list(self.project.iterdir()), before)

    def test_configured_context_does_not_fall_back_when_tool_missing(self):
        self.write_pointer(); code, report = self.invoke()
        self.assertEqual(code, 2); self.assertEqual(report["routing"], "blocked")
        self.assertEqual(report["diagnostics"][0]["code"], "COORDINATOR_UNAVAILABLE")
        code, report = self.invoke("--coordinator-skill", self.root / "missing-skill")
        self.assertEqual(code, 2); self.assertEqual(report["diagnostics"][0]["code"], "COORDINATOR_UNAVAILABLE")

    def test_invocation_errors_are_exit_three(self):
        code, report = self.invoke("--unknown", "not-echoed")
        self.assertEqual(code, 3); self.assertEqual(report["diagnostics"][0]["code"], "CLI_INVALID")
        result = subprocess.run([sys.executable, str(SCRIPT)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 3); self.assertEqual(result.stderr, "")

    def test_invalid_and_broken_context_block(self):
        path = self.write_pointer(); path.write_text('{"x":true,"x":false}')
        code, report = self.invoke("--coordinator-skill", COORDINATOR, "--initiative", self.initiative)
        self.assertEqual(code, 2); self.assertEqual(report["routing"], "blocked")
        path.unlink()
        try: path.symlink_to(self.root / "absent")
        except (OSError, NotImplementedError): self.skipTest("Symlink unavailable")
        self.assertEqual(self.invoke()[1]["routing"], "blocked")

    def test_broken_context_parent_is_not_absence(self):
        try: (self.project / ".sdd").symlink_to(self.root / "missing-directory", target_is_directory=True)
        except (OSError, NotImplementedError): self.skipTest("Symlink unavailable")
        code, report = self.invoke()
        self.assertEqual(code, 2); self.assertEqual(report["routing"], "blocked")

    def test_pointer_current_but_org_gate_remains_pending_no_local_mutations(self):
        self.write_pointer()
        for name in ("REQUIREMENTS.md", "DESIGN.md", "TASKS.md"):
            (self.project / name).write_text("Local authoritative unchanged")
        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        code, report = self.invoke("--coordinator-skill", COORDINATOR, "--initiative", self.initiative)
        self.assertEqual(code, 0); self.assertEqual(report["routing"], "participating")
        self.assertFalse(report["readiness_evaluated"])
        gate = subprocess.run([sys.executable, str(COORDINATOR / "scripts" / "validate_org.py"), "--initiative", str(self.initiative), "--mode", "readiness", "--handoff", "work", "--stage", "planning"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        self.assertEqual(gate.returncode, 2)
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_stale_pointer_wrong_handoff_and_explicit_session(self):
        self.pointer["initiative_digest"] = "sha256:" + "f" * 64
        path = self.write_pointer()
        self.assertEqual(self.invoke("--coordinator-skill", COORDINATOR, "--initiative", self.initiative)[1]["diagnostics"][0]["code"], "DIGEST_MISMATCH")
        self.pointer["initiative_digest"] = record_digest(self.records[0]); self.pointer["handoff_ids"] = ["api"]; self.write_pointer()
        self.assertEqual(self.invoke("--coordinator-skill", COORDINATOR, "--initiative", self.initiative)[0], 2)
        self.pointer["handoff_ids"] = ["work"]; path = self.write_pointer()
        session = self.root / "session.json"; path.replace(session)
        code, report = self.invoke("--context", session, "--coordinator-skill", COORDINATOR, "--initiative", self.initiative)
        self.assertEqual(code, 0); self.assertEqual(report["routing"], "participating")
        self.assertFalse(path.exists())

    def test_isolated_skills_are_not_assumed_adjacent(self):
        lifecycle = self.root / "one" / "lifecycle"; coordinator = self.root / "elsewhere" / "coordinator"
        shutil.copytree(REPO / "run-sdd-lifecycle", lifecycle)
        shutil.copytree(COORDINATOR, coordinator, ignore=shutil.ignore_patterns("__pycache__"))
        self.write_pointer()
        code, report = self.invoke("--coordinator-skill", coordinator, "--initiative", self.initiative, script=lifecycle / "scripts" / "inspect_participation.py")
        self.assertEqual(code, 0); self.assertEqual(report["routing"], "participating")


if __name__ == "__main__": unittest.main()

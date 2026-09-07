from tests.org_helpers import draft, write_bundle
from pathlib import Path
import ast
import json
import re
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1] / "coordinate-org-sdd"


class Skill(unittest.TestCase):
    def test_discoverable_metadata_and_self_contained_resources(self):
        text = (SKILL / "SKILL.md").read_text()
        frontmatter = text.split("---", 2)[1]
        fields = dict(line.split(": ", 1) for line in frontmatter.strip().splitlines())
        self.assertEqual(fields["name"], SKILL.name)
        self.assertTrue(fields["description"].strip())
        for target in re.findall(r"\]\(([^)]+)\)", text):
            self.assertTrue((SKILL / target).is_file(), target)
            self.assertTrue((SKILL / target).resolve().is_relative_to(SKILL))
        metadata = {}
        for line in (SKILL / "agents" / "openai.yaml").read_text().splitlines():
            if line.startswith("  ") and ": " in line:
                key, value = line.strip().split(": ", 1)
                metadata[key] = ast.literal_eval(value)
        self.assertTrue(metadata["display_name"])
        self.assertTrue(25 <= len(metadata["short_description"]) <= 64)
        self.assertIn("$" + SKILL.name, metadata["default_prompt"])

    def test_resource_links_resolve_within_package(self):
        operations = SKILL / "references" / "operations.md"
        for target in re.findall(r"\]\(([^)]+)\)", operations.read_text()):
            path = (operations.parent / target).resolve()
            self.assertTrue(path.is_relative_to(SKILL)); self.assertTrue(path.is_file())

    def test_new_unresolved_scope_inspection_is_read_only_and_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = write_bundle(directory, [draft()]); before = (root / "initiative.json").read_bytes()
            commands = [sys.executable, str(SKILL / "scripts" / "validate_org.py"), "--initiative", str(root), "--format", "json"]
            structure = subprocess.run(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            readiness = subprocess.run(commands + ["--mode", "readiness"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            self.assertEqual(structure.returncode, 0)
            self.assertEqual(readiness.returncode, 2)
            data = json.loads(readiness.stdout)
            self.assertTrue({"OWNER_UNRESOLVED", "POLICY_UNRESOLVED"} <= {d["code"] for d in data["diagnostics"]})
            self.assertFalse(any(s["state"] == "ready" for s in data["states"]))
            self.assertEqual((root / "initiative.json").read_bytes(), before)
            self.assertFalse((root / "approvals").exists())


if __name__ == "__main__": unittest.main()

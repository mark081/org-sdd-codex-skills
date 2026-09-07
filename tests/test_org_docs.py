"""Run documented commands and install blocks only in isolated destinations."""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
TUTORIAL = ROOT / "docs/organizational-sdd-tutorial.md"
ADOPTION = ROOT / "docs/organizational-sdd-adoption.md"
NAMES = ("analyze-brownfield-context", "spec-to-task-plan", "execute-task-waves",
         "run-sdd-lifecycle", "coordinate-org-sdd")


def install_block(marker):
    match = re.search(r"<!-- " + re.escape(marker) + r" -->\s*```[^\n]+\n(.*?)\n```",
                      README.read_text(encoding="utf-8"), re.S)
    if match is None:
        raise AssertionError(f"Missing executable install example: {marker}")
    return match.group(1)


class Documentation(unittest.TestCase):
    def test_local_documentation_links_resolve(self):
        for doc in (README, TUTORIAL, ADOPTION):
            text = re.sub(r"```.*?```", "", doc.read_text(encoding="utf-8"), flags=re.S)
            targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
            self.assertTrue(targets)
            for target in targets:
                if "://" in target or target.startswith("#"):
                    continue
                path = target.split("#", 1)[0]
                with self.subTest(doc=doc.name, target=target):
                    self.assertTrue((doc.parent / path).exists())
        for name in NAMES:
            self.assertTrue((ROOT / name / "SKILL.md").is_file())
            self.assertIn(f"({name}/SKILL.md)", README.read_text(encoding="utf-8"))

    def test_tutorial_commands_match_snapshot_contract_and_real_results(self):
        manifest = json.loads((ROOT / "examples/three-team/manifest.json").read_text())
        snapshots = {entry["id"]: entry for entry in manifest["snapshots"]}
        text = TUTORIAL.read_text(encoding="utf-8")
        commands = set(re.findall(r"^python(?:3)? (examples/three-team/run_example.py .+)$", text, re.M))
        observed = set()
        for command in sorted(commands):
            args = shlex.split(command)
            snapshot = args[args.index("--snapshot") + 1]
            entry = snapshots[snapshot]
            if "--stage" in args or "--allow-illustrative" not in args:
                expected = 2
            else:
                expected = entry["illustrative_readiness_exit"]
                observed.add(snapshot)
            result = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True,
                                    text=True, timeout=30)
            with self.subTest(command=command):
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                report = json.loads(result.stdout)
                self.assertTrue(report["illustrative"])
                self.assertTrue(report["structural_valid"])
                if "--stage" not in args and "--allow-illustrative" in args:
                    self.assertEqual(report["scope"]["stage"], entry["stage"])
                    self.assertEqual(report["scope"]["handoff_id"], entry["handoff"])
                    self.assertTrue(set(entry["expected_codes"]) <= {d["code"] for d in report["diagnostics"]})
        self.assertEqual(observed, set(snapshots))

    def test_documented_local_commands_run_without_changing_plans(self):
        text = TUTORIAL.read_text(encoding="utf-8")
        commands = re.findall(r"^python ((?:spec-to-task-plan|execute-task-waves)/scripts/.+)$", text, re.M)
        self.assertEqual(len(commands), 3)
        task = ROOT / "examples/three-team/sources/v1/catalog/TASKS.md"
        before = task.read_bytes()
        for command in commands:
            result = subprocess.run([sys.executable, *shlex.split(command)], cwd=ROOT,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(task.read_bytes(), before)


class InstallationExamples(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="org-doc-install-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "source checkout"
        self.repo.mkdir()
        self.codex = self.base / "isolated codex"
        self.skills = self.codex / "skills"
        self.env = dict(os.environ, CODEX_HOME=str(self.codex))
        for name in NAMES:
            source = self.repo / name
            source.mkdir()
            (source / "SKILL.md").write_text(f"Synthetic {name}\n", encoding="utf-8")
            (source / ".hidden-asset").write_text("preserve hidden assets", encoding="utf-8")
        self.pwsh = shutil.which("pwsh")

    def run_install(self, shell, mode=None):
        if shell == "posix":
            if os.name == "nt" or not shutil.which("sh"):
                self.skipTest("Native POSIX shell execution unavailable on this host")
            command = ["sh", "-c", install_block("install-posix")]
            env = dict(self.env, SDD_INSTALL_MODE=mode or "link")
        else:
            if not self.pwsh:
                self.skipTest("PowerShell unavailable; native PowerShell execution not verified")
            script = install_block("install-powershell")
            if mode:
                script = script.rsplit("Install-SddSkills", 1)[0] + f"Install-SddSkills -Mode {mode}"
            command = [self.pwsh, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script]
            env = self.env
        return subprocess.run(command, cwd=self.repo, env=env, capture_output=True,
                              text=True, timeout=30)

    def assert_installed(self, linked):
        self.assertEqual({p.name for p in self.skills.iterdir()}, set(NAMES))
        for name in NAMES:
            path = self.skills / name
            self.assertEqual(path.is_symlink(), linked)
            self.assertEqual((path / "SKILL.md").read_bytes(), (self.repo / name / "SKILL.md").read_bytes())
            self.assertEqual((path / ".hidden-asset").read_text(), "preserve hidden assets")

    def test_posix_install_links_all_five_using_codex_home(self):
        result = self.run_install("posix")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_installed(True)

    def test_posix_copy_contains_hidden_assets_and_remains_independent(self):
        result = self.run_install("posix", "copy")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_installed(False)
        original = (self.skills / NAMES[0] / "SKILL.md").read_bytes()
        (self.repo / NAMES[0] / "SKILL.md").write_text("updated source")
        self.assertEqual((self.skills / NAMES[0] / "SKILL.md").read_bytes(), original)

    def check_occupied(self, shell, kind):
        self.skills.mkdir(parents=True)
        target = self.skills / NAMES[-1]
        if kind == "file":
            target.write_text("preserve existing")
        elif kind == "directory":
            target.mkdir()
            (target / "sentinel").write_text("preserve existing")
        else:
            try:
                target.symlink_to(self.base / "missing-target", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation unavailable; broken-link case not verified")
            original_link = os.readlink(target)
        result = self.run_install(shell)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        # The last destination is occupied: all five were preflighted before any install.
        self.assertEqual({p.name for p in self.skills.iterdir()}, {NAMES[-1]})
        if kind == "file":
            self.assertEqual(target.read_text(), "preserve existing")
        elif kind == "directory":
            self.assertEqual((target / "sentinel").read_text(), "preserve existing")
        else:
            self.assertTrue(target.is_symlink())
            self.assertEqual(os.readlink(target), original_link)

    def test_posix_existing_file_preserved_before_any_install(self):
        self.check_occupied("posix", "file")

    def test_posix_existing_directory_preserved_before_any_install(self):
        self.check_occupied("posix", "directory")

    def test_posix_broken_symlink_preserved_before_any_install(self):
        self.check_occupied("posix", "broken")

    def test_powershell_copy_all_five_using_codex_home(self):
        result = self.run_install("powershell")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_installed(False)

    def test_powershell_symbolic_links_all_five(self):
        probe = self.base / "symlink-probe"
        try:
            probe.symlink_to(self.repo, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Directory symlink creation not permitted on this host")
        result = self.run_install("powershell", "SymbolicLink")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_installed(True)

    @unittest.skipUnless(os.name == "nt", "Native Windows junction behavior unverified on this host")
    def test_powershell_junctions_all_five(self):
        result = self.run_install("powershell", "Junction")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in NAMES:
            self.assertTrue(os.path.samefile(self.skills / name, self.repo / name))
            self.assertEqual((self.skills / name / "SKILL.md").read_bytes(),
                             (self.repo / name / "SKILL.md").read_bytes())

    def test_powershell_existing_file_preserved_before_any_install(self):
        self.check_occupied("powershell", "file")

    def test_powershell_existing_directory_preserved_before_any_install(self):
        self.check_occupied("powershell", "directory")

    def test_powershell_broken_symlink_preserved_before_any_install(self):
        self.check_occupied("powershell", "broken")


if __name__ == "__main__":
    unittest.main()

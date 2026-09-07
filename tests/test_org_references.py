from tests.org_helpers import bundle, draft, ref, source
from org_sdd.references import (ReferenceFailure, SourceResolver, byte_digest, canonical_bytes,
                                policy_digest, record_digest, release_projection, validate_context, validate_repo_map)
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch


def mapping(root, basis="snapshot"):
    return dict(format_version="1.0", repositories=dict(coordination=dict(root=str(root), basis=basis)))


class References(unittest.TestCase):
    def test_canonical_identity(self):
        self.assertEqual(canonical_bytes({"é": "é", "a": [True, None]}), b'{"a":[true,null],"\xc3\xa9":"\xc3\xa9"}')
        self.assertNotEqual(canonical_bytes(["a", "b"]), canonical_bytes(["b", "a"]))
        self.assertNotEqual(byte_digest(b"a\n"), byte_digest(b"a\r\n"))
        self.assertNotEqual(canonical_bytes("é"), canonical_bytes("e\u0301"))
        for value in (float("nan"), 1, "\ud800", {1: "x"}):
            with self.assertRaises(ReferenceFailure): canonical_bytes(value)

    def test_record_policy_and_release_projection(self):
        records = bundle(); initiative = records[0]
        digest = record_digest(initiative); policy = policy_digest(initiative)
        changed = deepcopy(initiative); changed["scope"] += " change"
        self.assertNotEqual(record_digest(changed), digest)
        self.assertEqual(policy_digest(changed), policy)
        changed["policy"]["gates"] = [dict(gate="scope", required_roles=["owner"])]
        self.assertNotEqual(policy_digest(changed), policy)
        result = release_projection(initiative, [records[1], records[1]], [records[2]], [], [])
        self.assertEqual(len(result["contracts"]), 1)
        self.assertNotIn("approvals", result)
        drift = deepcopy(records[1]); drift["scope"] = "unknown field"
        with self.assertRaises(ReferenceFailure): record_digest(drift)
        drift = deepcopy(records[1]); drift["display_version"] = "new"
        with self.assertRaises(ReferenceFailure): release_projection(initiative, [records[1], drift], [records[2]], [], [])

    def test_context_and_map_shapes(self):
        context = dict(format_version="1.0", initiative_id="demo", repository_id="team", coordination=dict(type="git", url="https://example.invalid/repo", path="initiatives/demo"), initiative_digest=ref()["digest"], handoff_ids=["work"])
        self.assertEqual(validate_context(context), [])
        context["handoff_ids"] *= 2; self.assertTrue(validate_context(context))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(validate_repo_map(mapping(root), [], root), [])
            bad = mapping(root); bad["repositories"]["coordination"]["root"] = "~/not-expanded"
            self.assertTrue(validate_repo_map(bad, [], root))
            bad = mapping(root); bad["repositories"]["unknown"] = bad["repositories"].pop("coordination")
            self.assertTrue(validate_repo_map(bad, [], root))
            with tempfile.TemporaryDirectory() as other:
                self.assertTrue(validate_repo_map(mapping(Path(other)), [], root))

    def test_snapshot_and_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "source.txt").write_bytes(b"hello\r\n")
            resolver = SourceResolver(mapping(root), [], root)
            src = source(); src["digest"] = byte_digest(b"hello\r\n")
            result = resolver.resolve(src)
            self.assertTrue(result.valid); self.assertEqual(result.content, b"hello\r\n")
            self.assertIsNone(result.baseline["revision"])
            src["digest"] = byte_digest(b"different")
            self.assertEqual(resolver.resolve(src).diagnostics[0].code, "DIGEST_MISMATCH")
            src["repository_id"] = "absent"
            self.assertEqual(resolver.resolve(src).diagnostics[0].code, "REFERENCE_UNRESOLVED")

    def test_paths_symlinks_and_missing(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory); resolver = SourceResolver(mapping(root), [], root)
            for path in ("../outside", "/etc/passwd", "a:stream", "a\\b"):
                self.assertEqual(resolver.resolve(source(path)).diagnostics[0].code, "PATH_UNSAFE")
            self.assertEqual(resolver.resolve(source("missing")).diagnostics[0].code, "REFERENCE_UNRESOLVED")
            external = Path(outside) / "private"; external.write_bytes(b"secret")
            try: (root / "link").symlink_to(external)
            except (OSError, NotImplementedError): self.skipTest("Symlink unavailable")
            self.assertEqual(resolver.resolve(source("link")).diagnostics[0].code, "PATH_UNSAFE")

    def test_git_committed_bytes_and_type(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args): return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).strip()
            git("init"); (root / "source.txt").write_bytes(b"committed\n")
            git("add", "source.txt"); git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-m", "fixture")
            revision = git("rev-parse", "HEAD").decode()
            src = source(); src.update(basis="git", revision=revision, digest=byte_digest(b"committed\n"))
            resolver = SourceResolver(mapping(root, "git"), [], root)
            (root / "source.txt").write_bytes(b"working copy changed")
            with patch.dict(os.environ, {"GIT_DIR": "/bad", "GIT_WORK_TREE": "/bad", "GIT_OBJECT_DIRECTORY": "/bad", "GIT_INDEX_FILE": "/bad", "GIT_ALTERNATE_OBJECT_DIRECTORIES": "/bad"}):
                self.assertTrue(resolver.resolve(src).valid)
            self.assertEqual(SourceResolver(mapping(root), [], root).resolve(src).diagnostics[0].code, "REFERENCE_UNRESOLVED")
            src["revision"] = git("rev-parse", "HEAD:source.txt").decode()
            self.assertEqual(resolver.resolve(src).diagnostics[0].code, "FORMAT_INVALID")
            src["revision"] = revision
            try: (root / "link").symlink_to("source.txt")
            except (OSError, NotImplementedError): self.skipTest("Symlink creation unavailable; committed-byte assertions ran before this capability check")
            git("add", "link"); git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-m", "symlink")
            src.update(path="link", revision=git("rev-parse", "HEAD").decode())
            self.assertEqual(resolver.resolve(src).diagnostics[0].code, "PATH_UNSAFE")

    def test_git_tree_gitlink_alternates_and_partial_store(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args): return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).strip()
            git("init"); (root / "folder").mkdir(); (root / "folder" / "file").write_bytes(b"test")
            git("add", "folder"); git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-m", "fixture")
            revision = git("rev-parse", "HEAD").decode()
            git("update-index", "--add", "--cacheinfo", "160000," + revision + ",submodule")
            git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-m", "gitlink")
            resolver = SourceResolver(mapping(root, "git"), [], root)
            src = source(); src.update(basis="git", revision=git("rev-parse", "HEAD").decode())
            for path in ("folder", "submodule"):
                src["path"] = path
                self.assertEqual(resolver.resolve(src).diagnostics[0].code, "PATH_UNSAFE")
            src.update(path="folder/file", digest=byte_digest(b"test"))
            self.assertTrue(resolver.resolve(src).valid)
            alternate = root / ".git" / "objects" / "info" / "alternates"
            alternate.write_text("/not-authorized")
            self.assertEqual(resolver.resolve(src).diagnostics[0].code, "PATH_UNSAFE")
            alternate.unlink()
            (root / ".git" / "objects" / "pack" / "synthetic.promisor").write_text("")
            self.assertEqual(resolver.resolve(src).diagnostics[0].code, "REFERENCE_UNRESOLVED")

    def test_inert_path_and_bounded_git_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); resolver = SourceResolver(mapping(root, "git"), [], root)
            filename = "$(echo should-not-run)"; (root / filename).write_bytes(b"inert")
            src = source(filename); src["digest"] = byte_digest(b"inert")
            self.assertTrue(resolver.resolve(src).valid)
            src.update(basis="git", revision="a" * 40)
            with patch("org_sdd.references.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 10)):
                self.assertEqual(resolver.resolve(src).diagnostics[0].code, "REFERENCE_UNRESOLVED")


if __name__ == "__main__": unittest.main()

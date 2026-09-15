"""Evaluation-local caching: bounded reads without stale cross-run authority."""
from tests.org_helpers import source
from org_sdd.records import load_initiative
from org_sdd.references import SourceResolver, byte_digest
from org_sdd.readiness import ReadinessEvaluator
from pathlib import Path
from unittest.mock import patch
from dataclasses import asdict
from contextlib import nullcontext
import tempfile
import unittest


def benchmark():
    """Opt-in local comparison; no timing threshold in the regression suite."""
    from statistics import median
    from time import perf_counter
    for cached in (False, True):
        engine = evaluator()
        timings = []
        sources = nullcontext() if cached else patch.object(engine.resolver, "evaluation", return_value=nullcontext())
        indexes = nullcontext() if cached else patch.object(engine.approvals, "evaluation", return_value=nullcontext())
        with sources, indexes, patch.object(engine.resolver, "_snapshot", wraps=engine.resolver._snapshot) as reads:
            for _ in range(25):
                start = perf_counter()
                report = engine.evaluate(stage="release")
                timings.append(perf_counter() - start)
                if not report.ready: raise AssertionError(report.diagnostics)
            print(f"cached={cached} median_ms={median(timings) * 1000:.2f} reads_per_run={reads.call_count // 25}")

ROOT = Path(__file__).resolve().parents[1] / "examples/three-team"


def evaluator(snapshot="08-release"):
    mapping = dict(format_version="1.0", repositories={"coordination": dict(root=str(ROOT), basis="snapshot")})
    for team in ("catalog", "checkout", "analytics"):
        mapping["repositories"][team] = dict(root=str(ROOT / "sources/v2" / team), basis="snapshot")
    dataset = load_initiative(ROOT / "snapshots" / snapshot)
    resolver = SourceResolver(mapping, ["catalog", "checkout", "analytics"], ROOT)
    return ReadinessEvaluator(dataset, resolver, allow_illustrative=True)


class Optimization(unittest.TestCase):
    def test_snapshot_cache_scoped_and_sensitive_to_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "source.txt"
            path.write_bytes(b"original")
            mapping = dict(format_version="1.0", repositories={"coordination": dict(root=str(root), basis="snapshot")})
            resolver = SourceResolver(mapping, [], root)
            ref = source(); ref["digest"] = byte_digest(b"original")
            with patch.object(resolver, "_snapshot", wraps=resolver._snapshot) as reads:
                with resolver.evaluation():
                    self.assertTrue(resolver.resolve(ref).valid)
                    self.assertTrue(resolver.resolve(ref).valid)
                    self.assertEqual(reads.call_count, 1)
                    path.write_bytes(b"changed")
                    result = resolver.resolve(ref, "new-file", "new-id", "new-field")
                    self.assertFalse(result.valid)
                    self.assertEqual(result.diagnostics[0].file, "new-file")
                    path.unlink()
                    self.assertFalse(resolver.resolve(ref).valid)
                path.write_bytes(b"original")
                before = reads.call_count
                self.assertTrue(resolver.resolve(ref).valid)
                self.assertEqual(reads.call_count, before + 1)
                self.assertIsNone(resolver._cache)

    def test_cache_equivalence_and_read_reduction(self):
        for snapshot in ("05-breaking-change", "06-migration-resolution", "08-release", "09-refreshed-knowledge"):
            with self.subTest(snapshot=snapshot):
                engine = evaluator(snapshot)
                with patch.object(engine.resolver, "_snapshot", wraps=engine.resolver._snapshot) as reads:
                    optimized = asdict(engine.evaluate(stage="release"))
                    optimized_reads = reads.call_count
                with patch.object(engine.resolver, "evaluation", return_value=nullcontext()), patch.object(engine.approvals, "evaluation", return_value=nullcontext()):
                    with patch.object(engine.resolver, "_snapshot", wraps=engine.resolver._snapshot) as reads:
                        baseline = asdict(engine.evaluate(stage="release"))
                        baseline_reads = reads.call_count
                self.assertEqual(optimized, baseline)
                self.assertLess(optimized_reads, baseline_reads)
                if snapshot == "08-release":
                    self.assertLessEqual(optimized_reads, 19)
                    self.assertGreater(baseline_reads, 200)
                self.assertIsNone(engine.approvals._index)
                self.assertIsNone(engine.resolver._cache)

    def test_new_evaluation_observes_changed_policy_contract_and_approval(self):
        for change in ("policy", "contract", "approval"):
            engine = evaluator()
            self.assertTrue(engine.evaluate(stage="release").ready)
            if change == "policy":
                engine.initiative["policy"]["role_assignments"][0]["actors"] = []
            elif change == "contract":
                contract = next(r for r in engine.records.values() if r["kind"] == "contract")
                contract["display_version"] += "-changed"
            else:
                approval = next(r for r in engine.records.values() if r["kind"] == "approval" and r["gate"] == "release")
                approval["decision"] = "revoked"
            self.assertFalse(engine.evaluate(stage="release").ready, change)

    def test_cache_cleanup_on_exception(self):
        engine = evaluator()
        with patch.object(engine, "_evaluate", side_effect=RuntimeError("interrupted")):
            with self.assertRaises(RuntimeError): engine.evaluate(stage="release")
        self.assertIsNone(engine.approvals._index)
        self.assertIsNone(engine.resolver._cache)
        self.assertTrue(engine.evaluate(stage="release").ready)

    def test_cached_snapshot_cannot_escape_root_after_link_retarget(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            root = Path(directory)
            (root / "inside").write_bytes(b"same")
            outside = Path(other) / "outside"
            outside.write_bytes(b"same")
            link = root / "source.txt"
            try: link.symlink_to(root / "inside")
            except (OSError, NotImplementedError): self.skipTest("Symlink unavailable")
            mapping = dict(format_version="1.0", repositories={"coordination": dict(root=str(root), basis="snapshot")})
            resolver = SourceResolver(mapping, [], root)
            ref = source(); ref["digest"] = byte_digest(b"same")
            with resolver.evaluation():
                self.assertTrue(resolver.resolve(ref).valid)
                link.unlink(); link.symlink_to(outside)
                result = resolver.resolve(ref)
                self.assertFalse(result.valid)
                self.assertEqual(result.diagnostics[0].code, "PATH_UNSAFE")


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--benchmark"]:
        benchmark()
    else:
        unittest.main()

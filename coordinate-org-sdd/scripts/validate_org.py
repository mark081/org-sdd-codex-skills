#!/usr/bin/env python3
"""Read-only Organizational SDD validator. Installed-skill standalone entry point."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from org_sdd.diagnostics import Diagnostic
from org_sdd.graph import build_graph
from org_sdd.readiness import ReadinessEvaluator
from org_sdd.records import ID_RE, load_initiative, parse_json, valid_time, validate_record
from org_sdd.references import (ReferenceFailure, SourceResolver, byte_digest, canonical_bytes,
                                policy_digest, record_digest, release_projection, validate_repo_map)


class UsageError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default includes raw untrusted argument values.
        raise UsageError("Invalid arguments; run --help for supported options")


def parser():
    result = Parser(description="Validate recorded Organizational SDD structure or readiness without network, writes, or test execution.")
    result.add_argument("--initiative", metavar="DIRECTORY")
    result.add_argument("--coordination-root", metavar="DIRECTORY", help="Explicit coordination workspace root containing the initiative; defaults to initiative directory")
    result.add_argument("--mode", choices=("structure", "readiness"))
    result.add_argument("--format", choices=("text", "json"), default="text")
    result.add_argument("--handoff", metavar="ID")
    result.add_argument("--stage", choices=("planning", "execution", "local_complete", "integration", "release"))
    result.add_argument("--repo-map", metavar="FILE")
    result.add_argument("--allow-illustrative", action="store_true")
    result.add_argument("--as-of", metavar="TIME", help="Explicit timezone-qualified instant for expiring knowledge")
    result.add_argument("--candidate-task", action="append", metavar="ID", help="Repeat for already approved current-wave candidates; organizational filter only")
    result.add_argument("--digest", metavar="FILE")
    result.add_argument("--digest-kind", choices=("record", "source", "policy", "release_scope"))
    return result


def read_bytes(path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode): raise OSError("Input must be a regular file")
        return handle.read()


def read_json(path):
    return parse_json(read_bytes(path).decode("utf-8"))


class TrackingResolver(SourceResolver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verified = {}

    def resolve(self, *args, **kwargs):
        result = super().resolve(*args, **kwargs)
        if result.valid:
            baseline = result.baseline
            self.verified[canonical_bytes(baseline)] = baseline
        return result


def diagnostic(code, message, field="", file="<invocation>"):
    return dict(code=code, file=file, record_id=None, field=field, message=message)


def dedupe_diagnostics(items):
    values = [asdict(item) if isinstance(item, Diagnostic) else item for item in items]
    unique = {json.dumps(item, sort_keys=True): item for item in values}
    return sorted(unique.values(), key=lambda d: (d["file"], d["record_id"] or "", d["field"], d["code"]))


def base_report(mode, args=None):
    return dict(format_version="1.0", mode=mode, structural_valid=False,
                scope=dict(handoff_id=args.handoff if args else None, stage=args.stage if args else None),
                baseline=dict(initiative_digest=None, sources=[], as_of=args.as_of if args else None),
                illustrative=bool(args and args.allow_illustrative), states=[], diagnostics=[])


def validate_options(args):
    if args.as_of is not None and not valid_time(args.as_of): raise UsageError("Supply a timezone-qualified evaluation instant")
    if args.handoff is not None and not ID_RE.fullmatch(args.handoff): raise UsageError("Invalid handoff selector")
    if args.digest is not None:
        if args.digest_kind is None or args.mode is not None or args.handoff or args.stage or args.candidate_task is not None:
            raise UsageError("Digest operation requires a kind and cannot select readiness scope")
        if args.digest_kind != "release_scope" and any((args.initiative, args.coordination_root, args.repo_map, args.as_of, args.allow_illustrative)):
            raise UsageError("Simple digest operations accept only file, kind and output format")
        if args.digest_kind == "release_scope" and not args.initiative: raise UsageError("Release-scope digest requires an initiative")
    else:
        if args.digest_kind is not None or not args.initiative: raise UsageError("Validation requires an initiative")
        if (args.mode or "structure") != "readiness" and (args.handoff or args.stage or args.candidate_task is not None):
            raise UsageError("Scope selectors require readiness mode")
        if args.handoff and args.stage in ("integration", "release"): raise UsageError("Initiative stages cannot select a handoff")
        if args.candidate_task is not None and (not args.handoff or args.stage != "execution"):
            raise UsageError("Candidate filtering requires handoff execution scope")
        if args.candidate_task is not None and (len(set(args.candidate_task)) != len(args.candidate_task) or any(not item.strip() for item in args.candidate_task)):
            raise UsageError("Candidates must be unique nonempty current-wave IDs")


def load_inputs(args):
    dataset = load_initiative(args.initiative)
    coordination_root = Path(args.coordination_root).resolve(strict=True) if args.coordination_root else dataset.root
    if not coordination_root.is_dir() or not dataset.root.is_relative_to(coordination_root):
        raise UsageError("Explicit coordination root must contain the selected initiative")
    if not dataset.valid:
        return dataset, None
    registered = [p["repository_id"] for p in dataset.initiative["participants"]] if dataset.initiative else []
    if args.repo_map:
        try: mapping = read_json(args.repo_map)
        except (ValueError, UnicodeError): raise UsageError("Repo-map input must be strict JSON")
        errors = validate_repo_map(mapping, registered, coordination_root)
        if errors: raise UsageError("Repo-map input is invalid or overrides the explicit coordination root")
    else:
        mapping = dict(format_version="1.0", repositories=dict(coordination=dict(root=str(coordination_root), basis="snapshot")))
    # Caller selection authorizes only the explicit coordination root. A map may
    # choose Git basis, but never silently infer or enlarge that root.
    if "coordination" not in mapping["repositories"]:
        mapping["repositories"]["coordination"] = dict(root=str(coordination_root), basis="snapshot")
    resolver = TrackingResolver(mapping, registered, coordination_root)
    return dataset, resolver


def populate_baseline(report, dataset, resolver, args):
    report["baseline"] = dict(initiative_digest=record_digest(dataset.initiative) if dataset.initiative else None,
                              sources=[resolver.verified[key] for key in sorted(resolver.verified)] if resolver else [], as_of=args.as_of)
    report["illustrative"] = args.allow_illustrative or any(r["illustrative"] for r in dataset.records.values())


def readiness_fields(report, readiness):
    report["states"] = [dict(record_id=s.record_id, stage=s.stage, state="ready" if s.ready else "blocked",
                             diagnostic_codes=sorted({d.code for d in s.diagnostics})) for s in readiness.states]
    report["diagnostics"] = dedupe_diagnostics(readiness.diagnostics)
    report["handoff_current"] = readiness.handoff_current
    report["local_gate_verification_required"] = readiness.local_gate_verification_required


def run(args):
    validate_options(args)
    if args.digest is not None and args.digest_kind != "release_scope":
        report = dict(format_version="1.0", mode="digest", digest_kind=args.digest_kind, digest=None, illustrative=False, diagnostics=[])
        content = read_bytes(args.digest)
        if args.digest_kind == "source": report["digest"] = byte_digest(content); return report, 0
        try: record = parse_json(content.decode("utf-8"))
        except (ValueError, UnicodeError):
            report["diagnostics"] = [diagnostic("FORMAT_INVALID", "Digest input must be strict UTF-8 JSON")]; return report, 1
        errors = validate_record(record)
        if errors:
            report["diagnostics"] = dedupe_diagnostics(errors); return report, 1
        report["illustrative"] = record["illustrative"]
        try: report["digest"] = record_digest(record) if args.digest_kind == "record" else policy_digest(record)
        except ReferenceFailure as exc:
            report["diagnostics"] = [asdict(exc.diagnostic)]; return report, 1
        return report, 0
    dataset, resolver = load_inputs(args)
    mode = "digest" if args.digest else args.mode or "structure"
    report = base_report(mode, args)
    if mode == "digest": report.update(digest_kind="release_scope", digest=None)
    populate_baseline(report, dataset, resolver, args)
    report["structural_valid"] = dataset.valid
    if not dataset.valid:
        report["diagnostics"] = dedupe_diagnostics(dataset.diagnostics); return report, 1
    if args.handoff is not None and (args.handoff not in dataset.records or dataset.records[args.handoff]["kind"] != "handoff"):
        raise UsageError("Selected handoff is unavailable")
    if mode == "structure":
        graph = build_graph(dataset)
        report["states"] = [dict(record_id=identity, stage=stage, state="not_evaluated", diagnostic_codes=[]) for identity, stage in sorted(graph.nodes)]
        return report, 0
    evaluator = ReadinessEvaluator(dataset, resolver, args.allow_illustrative, args.as_of)
    if mode == "digest":
        if Path(args.digest).resolve(strict=True) != (dataset.root / "initiative.json").resolve(strict=True):
            raise UsageError("Release-scope digest input must be the selected initiative.json")
        readiness = evaluator.evaluate(stage="integration")
        report["scope"] = dict(handoff_id=None, stage="integration")
        readiness_fields(report, readiness)
        if readiness.ready:
            try:
                projection = release_projection(dataset.initiative,
                    [dataset.records[i] for i in dataset.initiative["required_contracts"]],
                    [dataset.records[i] for i in dataset.initiative["required_handoffs"]],
                    [dataset.records[i] for i in sorted(evaluator.selected_evidence)],
                    [dataset.records[i] for i in sorted(evaluator.selected_knowledge)])
                report["digest"] = byte_digest(canonical_bytes(projection))
            except ReferenceFailure as exc:
                report["diagnostics"] = [asdict(exc.diagnostic)]; populate_baseline(report, dataset, resolver, args); return report, 2
        populate_baseline(report, dataset, resolver, args)
        return report, 0 if readiness.ready else 2
    readiness = evaluator.evaluate(args.handoff, args.stage, args.candidate_task)
    readiness_fields(report, readiness)
    if args.candidate_task is not None:
        report["eligible_tasks"] = readiness.eligible_tasks
        report["blocked_tasks"] = {key: dedupe_diagnostics(value) for key, value in sorted(readiness.blocked_tasks.items())}
    populate_baseline(report, dataset, resolver, args)
    return report, 0 if readiness.ready else 2


def emit(report, output_format):
    if output_format == "json":
        print(json.dumps(report, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
        return
    print("ILLUSTRATIVE — NOT PRODUCTION AUTHORIZATION" if report.get("illustrative") else "Recorded prerequisites only — not authenticated authorization")
    print("Mode: " + report["mode"])
    if "structural_valid" in report: print("Structural validity: " + str(report["structural_valid"]).lower())
    if "scope" in report: print("Scope: " + json.dumps(report["scope"], sort_keys=True))
    if "baseline" in report: print("Evaluated baseline: " + json.dumps(report["baseline"], sort_keys=True))
    if "digest" in report: print("Digest: " + str(report["digest"]))
    for state in report.get("states", []): print(state["record_id"] + "/" + state["stage"] + ": " + state["state"])
    for identity, current in sorted(report.get("handoff_current", {}).items()): print(identity + " current: " + str(current).lower())
    if "eligible_tasks" in report: print("Eligible supplied candidates: " + json.dumps(report["eligible_tasks"]))
    for task, blockers in sorted(report.get("blocked_tasks", {}).items()):
        print("Blocked supplied candidate " + json.dumps(task) + ": " + ", ".join(sorted({d["code"] for d in blockers})))
    for d in report["diagnostics"]: print(d["code"] + " " + d["file"] + " " + d["field"] + ": " + d["message"])


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    output_format = "json" if "--format=json" in argv or any(argv[i:i+2] == ["--format", "json"] for i in range(len(argv))) else "text"
    args = None
    try:
        args = parser().parse_args(argv)
        output_format = args.format
        report, code = run(args)
    except UsageError:
        report = base_report("digest" if args and args.digest else "readiness" if args and args.mode == "readiness" else "structure")
        report["diagnostics"] = [diagnostic("CLI_INVALID", "Invalid invocation or local mapping; run --help and check explicit inputs")]
        code = 3
    except (OSError, RuntimeError):
        report = base_report("digest" if args and args.digest else "readiness" if args and args.mode == "readiness" else "structure", args)
        report["diagnostics"] = [diagnostic("IO_ERROR", "Top-level input could not be read safely")]
        code = 3
    except ReferenceFailure as exc:
        report = base_report("digest" if args and args.digest else "structure")
        report["diagnostics"] = [asdict(exc.diagnostic)]; code = 3
    if report["mode"] == "digest":
        report.setdefault("digest_kind", args.digest_kind if args else None)
        report.setdefault("digest", None)
    emit(report, output_format)
    return code


if __name__ == "__main__": raise SystemExit(main())

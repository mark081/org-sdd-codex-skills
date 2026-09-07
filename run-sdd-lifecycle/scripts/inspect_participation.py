#!/usr/bin/env python3
"""Read-only pointer check; no organizational readiness or local gate inference."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import stat
import sys


class UsageError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError("Invalid invocation")


def check(project, context=None, coordinator_skill=None, initiative=None):
    root = Path(project).resolve(strict=True)
    if not root.is_dir(): raise OSError("Project must be a directory")
    path = Path(context) if context is not None else root / ".sdd" / "org" / "context.json"
    report = dict(routing="standalone", pointer_valid=None, readiness_evaluated=False, diagnostics=[])
    def blocked(code, message):
        report.update(routing="blocked", pointer_valid=False)
        report["diagnostics"].append(dict(code=code, file="<participation>", record_id=None, field="", message=message))
        return report, 2
    if context is None and not os.path.lexists(path):
        for parent in (root / ".sdd", root / ".sdd" / "org"):
            if parent.is_symlink():
                try:
                    if not parent.resolve(strict=True).is_relative_to(root):
                        return blocked("PATH_UNSAFE", "Participation location escapes the local repository")
                except (OSError, RuntimeError):
                    return blocked("REFERENCE_UNRESOLVED", "Participation location is unavailable")
        return report, 0
    if context is None:
        try:
            if not path.resolve(strict=True).is_relative_to(root): return blocked("PATH_UNSAFE", "Participation pointer escapes the local repository")
        except (OSError, RuntimeError): return blocked("REFERENCE_UNRESOLVED", "Configured participation pointer is unavailable")
    if coordinator_skill is None:
        return blocked("COORDINATOR_UNAVAILABLE", "Load the installed coordinator through the skill catalog before checking explicit participation")
    try: installed = Path(coordinator_skill).resolve(strict=True)
    except (OSError, RuntimeError): return blocked("COORDINATOR_UNAVAILABLE", "Supply the available catalog-resolved coordination skill")
    if not (installed / "SKILL.md").is_file() or not (installed / "src" / "org_sdd" / "references.py").is_file():
        return blocked("COORDINATOR_UNAVAILABLE", "Supply the catalog-resolved installed coordination skill")
    sys.path.insert(0, str(installed / "src"))
    from org_sdd.records import load_initiative, parse_json
    from org_sdd.references import record_digest, validate_context
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(descriptor, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode): return blocked("PATH_UNSAFE", "Participation context must be a regular file")
            pointer = parse_json(handle.read().decode("utf-8"))
    except (OSError, ValueError, UnicodeError):
        return blocked("FORMAT_INVALID", "Explicit participation context is unreadable or malformed")
    errors = validate_context(pointer)
    if errors:
        report.update(routing="blocked", pointer_valid=False, diagnostics=[asdict(d) for d in errors]); return report, 2
    if initiative is None: return blocked("REFERENCE_UNRESOLVED", "Supply or confirm the local initiative; no locator is automatically followed")
    dataset = load_initiative(initiative)
    if not dataset.valid:
        report.update(routing="blocked", pointer_valid=False, diagnostics=[asdict(d) for d in dataset.diagnostics]); return report, 2
    if pointer["initiative_id"] != dataset.initiative["id"] or pointer["initiative_digest"] != record_digest(dataset.initiative):
        return blocked("DIGEST_MISMATCH", "Participation pointer does not match the selected initiative baseline")
    if pointer["repository_id"] not in {p["repository_id"] for p in dataset.initiative["participants"]}:
        return blocked("REFERENCE_UNRESOLVED", "Participation repository is not registered")
    if not pointer["handoff_ids"]: return blocked("REFERENCE_UNRESOLVED", "Explicit participation needs a registered handoff")
    for identity in pointer["handoff_ids"]:
        handoff = dataset.records.get(identity)
        if not handoff or handoff["kind"] != "handoff" or handoff["repository_id"] != pointer["repository_id"]:
            return blocked("REFERENCE_UNRESOLVED", "Participation handoff must belong to the receiving repository")
    report.update(routing="participating", pointer_valid=True, initiative_id=pointer["initiative_id"], repository_id=pointer["repository_id"], handoff_ids=pointer["handoff_ids"], initiative_digest=pointer["initiative_digest"])
    return report, 0


def main():
    parser = Parser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--context")
    parser.add_argument("--coordinator-skill")
    parser.add_argument("--initiative")
    try:
        args = parser.parse_args()
        report, code = check(args.project, args.context, args.coordinator_skill, args.initiative)
    except UsageError:
        report, code = dict(routing="blocked", pointer_valid=False, readiness_evaluated=False,
                            diagnostics=[dict(code="CLI_INVALID", file="<invocation>", record_id=None, field="", message="Invalid invocation; run --help")]), 3
    except (OSError, RuntimeError, ImportError):
        report, code = dict(routing="blocked", pointer_valid=False, readiness_evaluated=False,
                            diagnostics=[dict(code="IO_ERROR", file="<invocation>", record_id=None, field="", message="Required local input or installed coordinator is unavailable")]), 3
    print(json.dumps(report, sort_keys=True))
    return code


if __name__ == "__main__": raise SystemExit(main())

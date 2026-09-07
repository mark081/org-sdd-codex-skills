#!/usr/bin/env python3
"""Read-only example runner; writes only its own temporary machine-local map."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--coordinator-skill", required=True, type=Path)
    parser.add_argument("--example-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--mode", choices=("structure", "readiness"), default="readiness")
    parser.add_argument("--stage", choices=("planning", "execution", "local_complete", "integration", "release"))
    parser.add_argument("--handoff")
    parser.add_argument("--allow-illustrative", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    root = args.example_root.resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    selected = next((s for s in manifest["snapshots"] if s["id"] == args.snapshot), None)
    if selected is None or selected["source_version"] not in ("v1", "v2"):
        parser.error("Select a listed snapshot")
    initiative = (root / "snapshots" / selected["id"]).resolve(strict=True)
    if not initiative.is_relative_to(root): parser.error("Snapshot must remain inside example root")
    mapping = dict(format_version="1.0", repositories={"coordination": dict(root=str(root), basis="snapshot")})
    for team in ("catalog", "checkout", "analytics"):
        source_root = (root / "sources" / selected["source_version"] / team).resolve(strict=True)
        if not source_root.is_relative_to(root): parser.error("Source must remain inside example root")
        mapping["repositories"][team] = dict(root=str(source_root), basis="snapshot")
    script = args.coordinator_skill.resolve(strict=True) / "scripts" / "validate_org.py"
    with tempfile.TemporaryDirectory(prefix="org-sdd-example-") as directory:
        map_path = Path(directory) / "repo-map.json"
        map_path.write_text(json.dumps(mapping), encoding="utf-8")
        command = [sys.executable, str(script), "--initiative", str(initiative), "--coordination-root", str(root), "--repo-map", str(map_path), "--mode", args.mode, "--format", args.format]
        if args.mode == "readiness":
            command.extend(["--stage", args.stage or selected["stage"]])
            handoff = args.handoff or (selected["handoff"] if not args.stage else None)
            if handoff: command.extend(["--handoff", handoff])
        if args.allow_illustrative: command.append("--allow-illustrative")
        # Never read or execute an artifact's procedure/command string.
        return subprocess.run(command, shell=False, check=False).returncode


if __name__ == "__main__": raise SystemExit(main())

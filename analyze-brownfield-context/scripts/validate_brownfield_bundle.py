#!/usr/bin/env python3
"""Validate the strict producer contract for a brownfield OKF v0.2 bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


FRONTMATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.S)
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
ACTOR = re.compile(r"^(?:human:[^/\s]+|process:[^/\s]+|[^/\s]+/[^/\s]+)$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
RESERVED = {"index.md", "log.md"}
STATUS = {"draft", "stable", "deprecated"}
CURATION = {"generated", "reviewed", "conflicted", "stale"}
EXCLUDED_PREFIXES = (".sdd/knowledge/", "graphify-out/")
EXCLUDED_FILES = {"REQUIREMENTS.md", "DESIGN.md", "TASKS.md"}


def run_git(project: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args], cwd=project, capture_output=True, check=False
    )


def excluded(relative: str) -> bool:
    return relative in EXCLUDED_FILES or relative.startswith(EXCLUDED_PREFIXES)


def repository_state(
    project: Path,
) -> tuple[str | None, str | None, str | None, list[dict[str, str]] | None]:
    revision_result = run_git(project, ["rev-parse", "HEAD"])
    if revision_result.returncode != 0:
        return None, None, None, None
    revision = revision_result.stdout.decode().strip()
    files_result = run_git(
        project, ["ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    )
    untracked_result = run_git(project, ["ls-files", "--others", "--exclude-standard", "-z"])
    diff_result = run_git(
        project,
        [
            "diff",
            "--quiet",
            "HEAD",
            "--",
            ".",
            ":(exclude).sdd/knowledge/**",
            ":(exclude)graphify-out/**",
            ":(exclude)REQUIREMENTS.md",
            ":(exclude)DESIGN.md",
            ":(exclude)TASKS.md",
        ],
    )
    if (
        files_result.returncode != 0
        or untracked_result.returncode != 0
        or diff_result.returncode not in {0, 1}
    ):
        return revision, None, None, None

    paths = sorted(
        path.decode("utf-8", "surrogateescape")
        for path in files_result.stdout.split(b"\0")
        if path and not excluded(path.decode("utf-8", "surrogateescape"))
    )
    untracked = {
        path.decode("utf-8", "surrogateescape")
        for path in untracked_result.stdout.split(b"\0")
        if path and not excluded(path.decode("utf-8", "surrogateescape"))
    }
    entries: list[dict[str, str]] = []
    for relative in paths:
        path = project / relative
        if path.is_symlink():
            kind = "symlink"
            payload = os.readlink(path).encode("utf-8", "surrogateescape")
        elif path.is_file():
            kind = "untracked" if relative in untracked else "file"
            payload = path.read_bytes()
        else:
            kind = "deleted"
            payload = b""
        entries.append(
            {"path": relative, "kind": kind, "sha256": hashlib.sha256(payload).hexdigest()}
        )

    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    fingerprint = hashlib.sha256(encoded).hexdigest()
    state = "dirty" if diff_result.returncode == 1 or untracked else "clean"
    return revision, fingerprint, state, entries


def parse_frontmatter(
    path: Path, text: str, errors: list[str]
) -> dict[str, Any] | None:
    match = FRONTMATTER.match(text)
    if not match:
        errors.append(f"{path}: missing YAML frontmatter")
        return None
    try:
        value = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML frontmatter: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path}: frontmatter must be a mapping")
        return None
    return value


def valid_time(value: Any) -> bool:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
    else:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def check_actor_time(
    relative: Path, label: str, value: Any, errors: list[str]
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{relative}: {label} must be a mapping")
        return
    actor = value.get("by")
    if not isinstance(actor, str) or not ACTOR.fullmatch(actor):
        errors.append(f"{relative}: {label}.by must follow the OKF actor convention")
    if not valid_time(value.get("at")):
        errors.append(f"{relative}: {label}.at must be ISO 8601 with an explicit offset")


def check_concept(
    relative: Path,
    frontmatter: dict[str, Any],
    revision: str | None,
    fingerprint: str | None,
    worktree: str | None,
    errors: list[str],
) -> None:
    concept_type = frontmatter.get("type")
    if not isinstance(concept_type, str) or not concept_type.strip():
        errors.append(f"{relative}: concept frontmatter missing non-empty type")

    if frontmatter.get("status") not in STATUS:
        errors.append(f"{relative}: status must be draft, stable, or deprecated")

    sources = frontmatter.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append(f"{relative}: sources must be a non-empty list")
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, dict) or not isinstance(source.get("resource"), str):
                errors.append(f"{relative}: sources[{index}].resource is required")

    check_actor_time(relative, "generated", frontmatter.get("generated"), errors)
    verified = frontmatter.get("verified", [])
    verified_items = verified if isinstance(verified, list) else [verified]
    for index, item in enumerate(verified_items):
        check_actor_time(relative, f"verified[{index}]", item, errors)

    stale_after = frontmatter.get("stale_after")
    if stale_after is not None:
        if not valid_time(stale_after):
            errors.append(f"{relative}: stale_after must be ISO 8601 with an explicit offset")
        else:
            parsed = (
                stale_after
                if isinstance(stale_after, datetime)
                else datetime.fromisoformat(stale_after.replace("Z", "+00:00"))
            )
            if datetime.now(timezone.utc) >= parsed.astimezone(timezone.utc):
                errors.append(f"{relative}: stale_after has expired")

    recorded_revision = frontmatter.get("source_revision")
    if not isinstance(recorded_revision, str) or not recorded_revision:
        errors.append(f"{relative}: missing source_revision")
    elif revision and recorded_revision != revision:
        errors.append(
            f"{relative}: stale source_revision {recorded_revision}; current HEAD is {revision}"
        )

    recorded_fingerprint = frontmatter.get("source_fingerprint")
    if not isinstance(recorded_fingerprint, str) or not SHA256.fullmatch(recorded_fingerprint):
        errors.append(f"{relative}: source_fingerprint must be a lowercase SHA-256")
    elif fingerprint and recorded_fingerprint != fingerprint:
        errors.append(f"{relative}: source_fingerprint does not match current source state")

    recorded_worktree = frontmatter.get("source_worktree")
    if recorded_worktree not in {"clean", "dirty"}:
        errors.append(f"{relative}: source_worktree must be clean or dirty")
    elif worktree and recorded_worktree != worktree:
        errors.append(
            f"{relative}: source_worktree is {recorded_worktree}; current state is {worktree}"
        )

    curation = frontmatter.get("curation_status")
    if curation not in CURATION:
        errors.append(
            f"{relative}: curation_status must be generated, reviewed, conflicted, or stale"
        )
    elif curation in {"conflicted", "stale"}:
        errors.append(f"{relative}: curation_status {curation} blocks trusted handoff")


def changed_paths(
    recorded_entries: list[dict[str, Any]], current_entries: list[dict[str, str]]
) -> list[dict[str, str]]:
    recorded = {
        item.get("path"): (item.get("kind"), item.get("sha256"))
        for item in recorded_entries
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    current = {item["path"]: (item["kind"], item["sha256"]) for item in current_entries}
    changes: list[dict[str, str]] = []
    for path in sorted(set(recorded) | set(current)):
        before = recorded.get(path)
        after = current.get(path)
        if before == after:
            continue
        if before is None:
            change = "added"
        elif after is None:
            change = "deleted"
        else:
            change = "modified"
        changes.append({"path": path, "change": change})
    return changes


def validate(project: Path) -> list[str]:
    if yaml is None:
        return ["PyYAML is required; install it or run with `uv run --with pyyaml python ...`"]

    bundle = project / ".sdd" / "knowledge"
    index = bundle / "index.md"
    if not index.is_file():
        return ["missing .sdd/knowledge/index.md"]
    if not (bundle / "bundle-state.md").is_file():
        return ["missing .sdd/knowledge/bundle-state.md"]
    manifest_path = bundle / "source-manifest.json"
    if not manifest_path.is_file():
        return ["missing .sdd/knowledge/source-manifest.json"]

    errors: list[str] = []
    revision, fingerprint, worktree, entries = repository_state(project)
    if revision is None:
        errors.append("project must be a Git repository with an existing commit")
    elif fingerprint is None or worktree is None or entries is None:
        errors.append("unable to compute repository source fingerprint")

    try:
        recorded_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"source-manifest.json: invalid manifest: {exc}")
        recorded_manifest = None
    if isinstance(recorded_manifest, dict) and entries is not None:
        expected_metadata = {
            "schema_version": "1.0",
            "source_revision": revision,
            "source_fingerprint": fingerprint,
            "source_worktree": worktree,
            "entries": entries,
        }
        if recorded_manifest != expected_metadata:
            changes = changed_paths(recorded_manifest.get("entries", []), entries)
            paths = [item["path"] for item in changes]
            detail = ", ".join(paths[:20])
            suffix = " ..." if len(paths) > 20 else ""
            errors.append(
                "source-manifest.json: repository source state changed"
                + (f": {detail}{suffix}" if detail else "")
            )

    index_text = index.read_text(encoding="utf-8")
    for path in sorted(bundle.rglob("*.md")):
        relative = path.relative_to(bundle)
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER.match(text)

        if path.name in RESERVED:
            if path == index:
                frontmatter = parse_frontmatter(relative, text, errors)
                if frontmatter is not None:
                    if set(frontmatter) != {"okf_version"}:
                        errors.append(
                            f"{relative}: root index frontmatter may contain only okf_version"
                        )
                    if str(frontmatter.get("okf_version")) != "0.2":
                        errors.append(f"{relative}: okf_version must be 0.2")
            elif match:
                errors.append(f"{relative}: reserved file must not have frontmatter")
        else:
            frontmatter = parse_frontmatter(relative, text, errors)
            if frontmatter is not None:
                check_concept(
                    relative,
                    frontmatter,
                    revision,
                    fingerprint,
                    worktree,
                    errors,
                )

        for target in LINK.findall(text):
            target = target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith(("#", "mailto:")):
                continue
            resolved = (
                bundle / target.lstrip("/")
                if target.startswith("/")
                else path.parent / target
            ).resolve()
            if not resolved.exists():
                errors.append(f"{relative}: broken internal link {target}")

    root_links = LINK.findall(index_text)
    normalized_root_links = {link.split("#", 1)[0].removeprefix("./").lstrip("/") for link in root_links}
    if "bundle-state.md" not in normalized_root_links:
        errors.append("index.md: must link directly to bundle-state.md")
    if len(root_links) < 2:
        errors.append("index.md: must link to bundle state and another concept")
    return errors


def write_manifest(project: Path) -> int:
    revision, fingerprint, worktree, entries = repository_state(project)
    if not all((revision, fingerprint, worktree)) or entries is None:
        print("ERROR: unable to compute repository source manifest")
        return 1
    bundle = project / ".sdd" / "knowledge"
    bundle.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1.0",
        "source_revision": revision,
        "source_fingerprint": fingerprint,
        "source_worktree": worktree,
        "entries": entries,
    }
    path = bundle / "source-manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"OK: wrote {path} ({fingerprint})")
    return 0


def diff_manifest(project: Path) -> int:
    path = project / ".sdd" / "knowledge" / "source-manifest.json"
    try:
        recorded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": f"invalid manifest: {exc}"}))
        return 1
    revision, fingerprint, worktree, entries = repository_state(project)
    if not all((revision, fingerprint, worktree)) or entries is None:
        print(json.dumps({"status": "error", "error": "unable to compute source state"}))
        return 1
    changes = changed_paths(recorded.get("entries", []), entries)
    result = {
        "status": "changed" if changes else "current",
        "baseline": {
            "source_revision": recorded.get("source_revision"),
            "source_fingerprint": recorded.get("source_fingerprint"),
            "source_worktree": recorded.get("source_worktree"),
        },
        "current": {
            "source_revision": revision,
            "source_fingerprint": fingerprint,
            "source_worktree": worktree,
        },
        "changes": changes,
    }
    print(json.dumps(result, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--write-manifest", action="store_true")
    actions.add_argument("--diff-manifest", action="store_true")
    args = parser.parse_args()
    if args.write_manifest:
        return write_manifest(args.project.resolve())
    if args.diff_manifest:
        return diff_manifest(args.project.resolve())
    errors = validate(args.project.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: strict brownfield OKF v0.2 bundle validated for {args.project.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

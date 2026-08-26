#!/usr/bin/env python3
"""Validate REQUIREMENTS.md, DESIGN.md, and TASKS.md traceability."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQ_ID = re.compile(r"(?<![A-Z0-9])[A-Z][A-Z0-9]*-[A-Z][A-Z0-9]*-\d{3}(?![A-Z0-9])")
REQ_DEF = re.compile(r"^\*\*([A-Z][A-Z0-9]*-[A-Z][A-Z0-9]*-\d{3})\b", re.M)


def read(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"missing {path.name}")
    return path.read_text(encoding="utf-8")


def requirements(project: Path) -> tuple[str, set[str], list[str]]:
    text = read(project / "REQUIREMENTS.md")
    errors: list[str] = []
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        errors.append("REQUIREMENTS.md must contain YAML front matter")
    for key in ("title:", "version:", "status:"):
        if key not in text.split("---", 2)[1]:
            errors.append(f"front matter missing {key}")
    ids = REQ_DEF.findall(text)
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append("duplicate requirement IDs: " + ", ".join(duplicates))
    if not ids:
        errors.append("no requirement definitions found")
    for match in re.finditer(r"^\*\*([A-Z][A-Z0-9-]+).*?\n(.+?)(?=\n\n|\Z)", text, re.M | re.S):
        body = match.group(2).strip()
        if " shall " not in f" {body.lower()} ":
            errors.append(f"{match.group(1)} does not contain 'shall'")
    for heading in ("Glossary", "Open questions", "Decisions and remaining open questions"):
        if heading.lower() in text.lower():
            break
    else:
        errors.append("missing glossary/open-question governance sections")
    return text, set(ids), errors


def validate(project: Path, stage: str) -> list[str]:
    _, ids, errors = requirements(project)
    if stage in {"design", "tasks", "all"}:
        design = read(project / "DESIGN.md")
        missing = sorted(ids - set(REQ_ID.findall(design)))
        if missing:
            errors.append("DESIGN.md missing requirement references: " + ", ".join(missing))
        for heading in ("## Overview", "## Architecture", "## Components and Interfaces", "## Data Models", "## Correctness Properties", "## Error Handling", "## Testing Strategy"):
            if heading not in design:
                errors.append(f"DESIGN.md missing heading: {heading}")
    if stage in {"tasks", "all"}:
        tasks = read(project / "TASKS.md")
        missing = sorted(ids - set(REQ_ID.findall(tasks)))
        if missing:
            errors.append("TASKS.md missing requirement references: " + ", ".join(missing))
        if "## Task Dependency Graph" not in tasks:
            errors.append("TASKS.md missing dependency graph")
        if not re.search(r"^\s*- \[ \] \d+(?:\.\d+)?\.", tasks, re.M):
            errors.append("TASKS.md contains no unchecked numbered tasks")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--stage", choices=("requirements", "design", "tasks", "all"), default="all")
    args = parser.parse_args()
    try:
        errors = validate(args.project.resolve(), args.stage)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {args.stage} validation passed for {args.project.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate the fenced JSON wave graph embedded in TASKS.md."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from pathlib import Path


TASK = re.compile(r"^\s*- \[[ xX]\]\*?\s+(\d+(?:\.\d+)*)(?:\.)?\s+", re.M)
GRAPH = re.compile(r"## Task Dependency Graph.*?```json\s*(\{.*?\})\s*```", re.S)


def leaf_ids(task_ids):
    """Dotted ancestors are grouping tasks; all other tasks must be scheduled."""
    parents = {identity.rsplit('.', depth)[0]
               for identity in task_ids for depth in range(1, identity.count('.') + 1)}
    return set(task_ids) - parents


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks", type=Path)
    args = parser.parse_args()
    text = args.tasks.read_text(encoding="utf-8")
    declarations = TASK.findall(text)
    task_ids = set(declarations)
    match = GRAPH.search(text)
    if not match:
        print("ERROR: missing fenced JSON dependency graph")
        return 1
    try:
        graph = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid graph JSON: {exc}")
        return 1
    waves = graph.get("waves")
    if not isinstance(waves, list) or not waves:
        print("ERROR: graph.waves must be a non-empty list")
        return 1
    expected = list(range(len(waves)))
    actual = [wave.get("id") for wave in waves]
    errors: list[str] = []
    if actual != expected:
        errors.append(f"wave ids must be sequential {expected}; got {actual}")
    graph_tasks: list[str] = []
    for wave in waves:
        items = wave.get("tasks")
        if not isinstance(items, list) or not items:
            errors.append(f"wave {wave.get('id')} must contain tasks")
            continue
        graph_tasks.extend(str(item) for item in items)
    duplicate = sorted(item for item, count in Counter(graph_tasks).items() if count > 1)
    unknown = sorted(set(graph_tasks) - task_ids)
    missing = sorted(leaf_ids(task_ids) - set(graph_tasks))
    repeated = sorted(item for item, count in Counter(declarations).items() if count > 1)
    if repeated:
        errors.append("duplicate task declarations: " + ", ".join(repeated))
    if missing:
        errors.append("unscheduled leaf tasks: " + ", ".join(missing))
    if duplicate:
        errors.append("duplicate graph tasks: " + ", ".join(duplicate))
    if unknown:
        errors.append("graph references unknown tasks: " + ", ".join(unknown))
    if errors:
        for error in errors:
            print("ERROR: " + error)
        return 1
    print(f"OK: {len(waves)} waves, {len(graph_tasks)} scheduled tasks")
    return 0


if __name__ == "__main__":
    sys.exit(main())

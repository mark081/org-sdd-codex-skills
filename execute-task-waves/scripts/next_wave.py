#!/usr/bin/env python3
"""Report the first incomplete dependency wave in an embedded TASKS.md graph."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TASK_LINE = re.compile(r"^\s*- \[([ xX])\]\*?\s+(\d+(?:\.\d+)*)(?:\.)?\s+(.+)$", re.M)
GRAPH = re.compile(r"## Task Dependency Graph.*?```json\s*(\{.*?\})\s*```", re.S)


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    tasks = {
        task_id: {"complete": mark.lower() == "x", "title": title.strip()}
        for mark, task_id, title in TASK_LINE.findall(text)
    }
    match = GRAPH.search(text)
    if not match:
        raise ValueError("missing fenced JSON dependency graph")
    graph = json.loads(match.group(1))
    waves = graph.get("waves")
    if not isinstance(waves, list) or not waves:
        raise ValueError("graph.waves must be a non-empty list")
    ids = [wave.get("id") for wave in waves]
    if ids != list(range(len(waves))):
        raise ValueError("wave ids must be sequential from zero")
    scheduled: set[str] = set()
    for wave in waves:
        items = wave.get("tasks")
        if not isinstance(items, list) or not items:
            raise ValueError(f"wave {wave.get('id')} has no tasks")
        for item in map(str, items):
            if item not in tasks:
                raise ValueError(f"wave {wave.get('id')} references unknown task {item}")
            if item in scheduled:
                raise ValueError(f"task {item} appears in multiple waves")
            scheduled.add(item)
    for wave in waves:
        pending = [str(item) for item in wave["tasks"] if not tasks[str(item)]["complete"]]
        if pending:
            return {
                "status": "ready",
                "wave": wave["id"],
                "tasks": [
                    {"id": task_id, "title": tasks[task_id]["title"]}
                    for task_id in pending
                ],
                "all_prior_waves_complete": True,
            }
    return {"status": "complete", "wave": None, "tasks": [], "all_prior_waves_complete": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        result = parse(args.tasks)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())

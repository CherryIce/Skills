#!/usr/bin/env python3
"""Group explicitly supplied factory retrospectives; never modify the Skill."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
from typing import Any


KEY = re.compile(r"[a-z0-9][a-z0-9_.-]*\Z")
SEVERITIES = {"P0", "P1", "P2", "P3"}


def nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def load_record(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read {path}: {error}") from error
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"{path}: expected schema_version 1 object")
    if value.get("status") != "completed":
        raise ValueError(f"{path}: retrospective is not completed")
    run = value.get("run")
    if not isinstance(run, dict):
        raise ValueError(f"{path}: run must be an object")
    for field in ("run_id", "project_ref", "scope", "product_verdict"):
        nonempty(run.get(field), f"{path}: run.{field}")
    lessons = value.get("lessons")
    if not isinstance(lessons, list):
        raise ValueError(f"{path}: lessons must be an array")
    for index, lesson in enumerate(lessons):
        label = f"{path}: lessons[{index}]"
        if not isinstance(lesson, dict):
            raise ValueError(f"{label} must be an object")
        key = nonempty(lesson.get("pattern_key"), f"{label}.pattern_key")
        if not KEY.fullmatch(key):
            raise ValueError(f"{label}.pattern_key must be a lowercase slug")
        if lesson.get("severity") not in SEVERITIES:
            raise ValueError(f"{label}.severity must be P0, P1, P2, or P3")
        if lesson.get("cause_confidence") not in ("confirmed", "hypothesis", "unknown"):
            raise ValueError(f"{label}.cause_confidence is invalid")
        for field in ("symptom", "phase", "cause", "proposed_change", "regression_check"):
            nonempty(lesson.get(field), f"{label}.{field}")
        evidence = lesson.get("evidence")
        if not isinstance(evidence, list) or any(
            not isinstance(ref, str) or not ref.strip() for ref in evidence
        ):
            raise ValueError(f"{label}.evidence must be an array of references")
    return value


def summarize(records: list[dict[str, Any]]) -> list[tuple[str, int, int, str, str]]:
    groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"projects": set(), "runs": set(), "confirmed_projects": set(),
                 "p0_confirmed": False, "severities": set()}
    )
    for record in records:
        run = record["run"]
        for lesson in record["lessons"]:
            item = groups[lesson["pattern_key"]]
            item["projects"].add(run["project_ref"])
            item["runs"].add(run["run_id"])
            item["severities"].add(lesson["severity"])
            if lesson["cause_confidence"] == "confirmed" and lesson["evidence"]:
                item["confirmed_projects"].add(run["project_ref"])
                if lesson["severity"] == "P0":
                    item["p0_confirmed"] = True
    rows = []
    for key, item in sorted(groups.items()):
        if item["p0_confirmed"]:
            flag = "urgent_review"
        elif len(item["confirmed_projects"]) >= 2:
            flag = "review_candidate"
        else:
            flag = "more_evidence_needed"
        highest = min(item["severities"], key=lambda severity: int(severity[1]))
        rows.append((key, len(item["projects"]), len(item["runs"]), highest, flag))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path, nargs="+", help="Explicit completed JSON paths")
    args = parser.parse_args()
    try:
        records = [load_record(path) for path in args.records]
        run_ids = [record["run"]["run_id"] for record in records]
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("Duplicate run_id across supplied records")
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    print("# Factory learning candidates\n")
    print("Only supplied records were read. Flags request human review, not Skill changes.\n")
    print("| Pattern key | Distinct projects | Runs | Highest severity | Flag |")
    print("| --- | ---: | ---: | --- | --- |")
    for key, projects, runs, severity, flag in summarize(records):
        print(f"| `{key}` | {projects} | {runs} | {severity} | `{flag}` |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

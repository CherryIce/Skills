#!/usr/bin/env python3
"""Render App Product Factory documentation templates into a project.

This script only creates documentation. It never modifies application source,
build settings, accounts, certificates, or external services.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "templates"
SAMPLE_CONFIG = TEMPLATE_ROOT / "intake.json"
TOKEN_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
REQUIRED_KEYS = (
    "app_name",
    "working_name",
    "target_user",
    "problem",
    "core_loop",
    "scope",
)
SCOPE_TEMPLATES = {
    "discovery": {
        "docs/product/MARKET_EVIDENCE.md.tmpl",
        "docs/product/DIFFERENTIATION.md.tmpl",
    },
    "product_design": {
        "docs/product/MARKET_EVIDENCE.md.tmpl",
        "docs/product/PRODUCT_BRIEF.md.tmpl",
        "docs/product/DIFFERENTIATION.md.tmpl",
    },
    "mvp": {
        "docs/product/MARKET_EVIDENCE.md.tmpl",
        "docs/product/PRODUCT_BRIEF.md.tmpl",
        "docs/product/DIFFERENTIATION.md.tmpl",
        "docs/release/FUNCTIONAL_REVIEW.md.tmpl",
        "docs/release/EVIDENCE_REGISTER.md.tmpl",
        "docs/release/GAP_BACKLOG.md.tmpl",
    },
    "audit": {
        "docs/product/MARKET_EVIDENCE.md.tmpl",
        "docs/product/PRODUCT_BRIEF.md.tmpl",
        "docs/product/DIFFERENTIATION.md.tmpl",
        "docs/release/FUNCTIONAL_REVIEW.md.tmpl",
        "docs/release/EVIDENCE_REGISTER.md.tmpl",
        "docs/release/GAP_BACKLOG.md.tmpl",
    },
    "release_candidate": {
        "docs/product/MARKET_EVIDENCE.md.tmpl",
        "docs/product/PRODUCT_BRIEF.md.tmpl",
        "docs/product/DIFFERENTIATION.md.tmpl",
        "docs/release/FUNCTIONAL_REVIEW.md.tmpl",
        "docs/release/APP_STORE_PREFLIGHT.md.tmpl",
        "docs/release/EVIDENCE_REGISTER.md.tmpl",
        "docs/release/GAP_BACKLOG.md.tmpl",
        "docs/release/PRIVACY_POLICY_DRAFT.md.tmpl",
        "docs/release/REVIEW_NOTES_DRAFT.md.tmpl",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a factory intake file or render review document templates."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--init-config",
        type=Path,
        metavar="PATH",
        help="Write a copy of the editable intake JSON and exit.",
    )
    mode.add_argument(
        "--project",
        type=Path,
        metavar="DIR",
        help="Existing project directory that will receive rendered documents.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Completed intake JSON. Required with --project.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing rendered documents. Use only intentionally.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List destination files without writing them.",
    )
    return parser.parse_args()


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def write_initial_config(destination: Path, force: bool, dry_run: bool) -> int:
    destination = destination.expanduser().resolve()
    if destination.exists() and not force:
        print(f"Refusing to overwrite existing config: {destination}", file=sys.stderr)
        return 2
    print(f"CREATE {destination}")
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SAMPLE_CONFIG, destination)
    return 0


def load_config(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read intake JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("The intake JSON root must be an object.")
    missing = [key for key in REQUIRED_KEYS if not str(value.get(key, "")).strip()]
    if missing:
        raise ValueError(f"Missing required intake fields: {', '.join(missing)}")
    scope = str(value["scope"]).strip()
    if scope not in SCOPE_TEMPLATES:
        choices = ", ".join(SCOPE_TEMPLATES)
        raise ValueError(f"Unsupported scope {scope!r}; choose one of: {choices}")
    return value


def markdown_value(value: Any) -> str:
    text = str(value).strip().replace("|", "\\|")
    return "<br>".join(part.strip() for part in text.splitlines())


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, list):
        if not value:
            return "[未提供]"
        return "<br>".join(markdown_value(item) for item in value)
    if value is None or not str(value).strip():
        return "[未提供]"
    if isinstance(value, dict):
        return markdown_value(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return markdown_value(value)


def token_map(config: dict[str, Any], required_tokens: set[str]) -> dict[str, str]:
    now = dt.datetime.now(dt.timezone.utc).astimezone()
    values = {key.upper(): format_value(value) for key, value in config.items()}
    values.update(
        {
            "RUN_DATE": now.date().isoformat(),
            "GENERATED_AT": now.isoformat(timespec="seconds"),
        }
    )
    for key in required_tokens:
        values.setdefault(key, "[未提供]")
    return values


def render(template: str, values: dict[str, str], source: Path) -> str:
    missing: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            missing.add(key)
            return match.group(0)
        return values[key]

    rendered = TOKEN_PATTERN.sub(replace, template)
    if missing:
        raise ValueError(
            f"Template {source} requires missing values: {', '.join(sorted(missing))}"
        )
    return rendered


def render_documents(
    project: Path, config_path: Path, force: bool, dry_run: bool
) -> int:
    project = project.expanduser().resolve()
    config_path = config_path.expanduser().resolve()
    if not project.is_dir():
        print(f"Project directory does not exist: {project}", file=sys.stderr)
        return 2
    try:
        config = load_config(config_path)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    allowed = SCOPE_TEMPLATES[str(config["scope"]).strip()]
    templates = [
        source
        for source in sorted(TEMPLATE_ROOT.glob("docs/**/*.tmpl"))
        if source.relative_to(TEMPLATE_ROOT).as_posix() in allowed
    ]
    if not templates:
        print(f"No documentation templates found under {TEMPLATE_ROOT}", file=sys.stderr)
        return 2

    try:
        template_inputs = [(source, source.read_text(encoding="utf-8")) for source in templates]
        required_tokens = {
            token
            for _, template in template_inputs
            for token in TOKEN_PATTERN.findall(template)
        }
        values = token_map(config, required_tokens)
        rendered_documents = [
            (source, render(template, values, source))
            for source, template in template_inputs
        ]
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2

    created: list[Path] = []
    skipped: list[Path] = []
    planned: list[tuple[Path, str]] = []
    for source, content in rendered_documents:
        relative = source.relative_to(TEMPLATE_ROOT)
        destination = project / Path(str(relative)[: -len(".tmpl")])
        if destination.exists() and not force:
            skipped.append(destination)
            continue
        planned.append((destination, content))

    for destination, content in planned:
        print(f"{'WOULD CREATE' if dry_run else 'CREATE'} {destination}")
        if not dry_run:
            atomic_write(destination, content)
        created.append(destination)

    intake_destination = project / "docs" / "product" / "FACTORY_INTAKE.json"
    if intake_destination.exists() and not force:
        skipped.append(intake_destination)
    else:
        print(f"{'WOULD CREATE' if dry_run else 'CREATE'} {intake_destination}")
        if not dry_run:
            normalized = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
            atomic_write(intake_destination, normalized)
        created.append(intake_destination)

    print(f"Rendered: {len(created)}; skipped existing: {len(skipped)}")
    for path in skipped:
        print(f"SKIP {path}")
    return 0


def main() -> int:
    args = parse_args()
    if args.init_config is not None:
        return write_initial_config(args.init_config, args.force, args.dry_run)
    if args.config is None:
        print("--config is required with --project", file=sys.stderr)
        return 2
    return render_documents(args.project, args.config, args.force, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())

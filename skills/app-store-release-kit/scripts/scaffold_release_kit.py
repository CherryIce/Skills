#!/usr/bin/env python3
"""Create a non-destructive per-app release-kit manifest."""

from __future__ import annotations

import argparse
import plistlib
import re
from datetime import date
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_ROOT / "assets" / "release-kit.yml.tmpl"
IGNORED_DIRS = {".dart_tool", ".git", "build", "Pods", "node_modules"}


def find_app_root(candidate: Path) -> Path:
    candidate = candidate.resolve()
    if not candidate.is_dir():
        raise SystemExit(f"App path is not a directory: {candidate}")
    if (candidate / "pubspec.yaml").is_file():
        return candidate

    matches: list[Path] = []
    for path in candidate.rglob("pubspec.yaml"):
        relative = path.relative_to(candidate)
        if len(relative.parts) > 4 or any(part in IGNORED_DIRS for part in relative.parts):
            continue
        matches.append(path.parent)
    matches.sort(key=lambda path: (len(path.relative_to(candidate).parts), str(path)))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        return candidate
    rendered = "\n".join(f"- {path}" for path in matches)
    raise SystemExit(f"Ambiguous app root; pass one of these directories directly:\n{rendered}")


def pubspec_name(root: Path) -> str:
    info_plist = root / "ios" / "Runner" / "Info.plist"
    if info_plist.is_file():
        try:
            payload = plistlib.loads(info_plist.read_bytes())
            display_name = payload.get("CFBundleDisplayName") or payload.get("CFBundleName")
            if isinstance(display_name, str) and display_name and not display_name.startswith("$("):
                return display_name
        except Exception:
            pass
    pubspec = root / "pubspec.yaml"
    if pubspec.is_file():
        match = re.search(r"(?m)^name:\s*['\"]?([^'\"#\n]+)", pubspec.read_text(errors="replace"))
        if match:
            raw = match.group(1).strip()
            return " ".join(part.capitalize() for part in re.split(r"[_-]+", raw))
    return root.name.replace("_", " ").replace("-", " ").title()


def display_path(root: Path) -> str:
    try:
        return str(root.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app_root", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Print the manifest without writing it")
    args = parser.parse_args()

    root = find_app_root(args.app_root)
    destination = root / "release-kit.yml"
    rendered = (
        TEMPLATE.read_text()
        .replace("[[APP_NAME]]", pubspec_name(root))
        .replace("[[APP_ROOT]]", display_path(root))
        .replace("[[GENERATED_DATE]]", date.today().isoformat())
    )

    if args.dry_run:
        print(rendered, end="")
        return
    if destination.exists():
        raise SystemExit(f"Refusing to overwrite existing manifest: {destination}")

    destination.write_text(rendered)
    (root / "artifacts" / "release-kit").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "app-store-listing").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "app-store-previews" / "source").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "app-store-previews" / "final").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "app-store-previews" / "qa").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "google-play-listing" / "source").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "google-play-listing" / "final").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "google-play-listing" / "qa").mkdir(parents=True, exist_ok=True)
    print(destination)


if __name__ == "__main__":
    main()

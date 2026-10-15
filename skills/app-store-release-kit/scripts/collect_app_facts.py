#!/usr/bin/env python3
"""Collect source-backed app signals without turning them into privacy conclusions."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


IGNORED_DIRS = {
    ".dart_tool",
    ".git",
    ".gradle",
    ".idea",
    ".symlinks",
    "Pods",
    "artifacts",
    "build",
    "docs",
    "node_modules",
    "qa-artifacts",
    "test",
    "website",
}
TEXT_SUFFIXES = {".dart", ".swift", ".m", ".mm", ".h", ".kt", ".java", ".xml", ".json", ".yaml", ".yml", ".plist"}
URL_PATTERN = re.compile(r"https?://[^\s\"'<>)}\]]+")
SIGNAL_GROUPS = {
    "analytics_or_diagnostics": ("analytics", "firebase_analytics", "firebase_crashlytics", "sentry", "crashlytics"),
    "advertising_or_attribution": ("admob", "advert", "appsflyer", "adjust", "facebook_app_events", "tracking_transparency"),
    "accounts_or_auth": ("auth", "sign_in", "oauth", "firebase_auth", "supabase"),
    "camera_or_photos": ("camera", "image_picker", "photo_manager", "photos"),
    "microphone_or_speech": ("microphone", "record", "speech_to_text", "speech"),
    "location": ("geolocator", "location", "maps"),
    "networking": ("http", "dio", "graphql", "web_socket", "firebase_core"),
    "payments": ("in_app_purchase", "purchases_flutter", "stripe", "payment"),
    "local_storage": ("sqflite", "drift", "hive", "isar", "shared_preferences", "realm"),
    "cloud_storage_or_sync": ("cloud", "firebase_storage", "cloud_firestore", "icloud", "cloudkit", "supabase"),
}


def find_app_root(candidate: Path) -> Path:
    candidate = candidate.resolve()
    if not candidate.is_dir():
        raise SystemExit(f"App path is not a directory: {candidate}")
    if (candidate / "pubspec.yaml").is_file():
        return candidate

    matches: list[Path] = []
    for current, dirs, files in os.walk(candidate):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS and not name.startswith(".")]
        current_path = Path(current)
        if len(current_path.relative_to(candidate).parts) > 3:
            dirs[:] = []
            continue
        if "pubspec.yaml" in files:
            matches.append(current_path)
    matches.sort(key=lambda path: (len(path.relative_to(candidate).parts), str(path)))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        return candidate
    rendered = "\n".join(f"- {path}" for path in matches)
    raise SystemExit(f"Ambiguous app root; pass one directory directly:\n{rendered}")


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(errors="replace")
    except OSError:
        return ""


def parse_pubspec(root: Path) -> dict[str, object]:
    path = root / "pubspec.yaml"
    if not path.is_file():
        return {"path": None, "name": None, "description": None, "version": None, "dependencies": []}

    text = read_text(path)
    result: dict[str, object] = {"path": str(path), "name": None, "description": None, "version": None, "dependencies": []}
    for key in ("name", "description", "version"):
        match = re.search(rf"(?m)^{key}:\s*['\"]?([^'\"#\n]+)", text)
        if match:
            result[key] = match.group(1).strip()

    dependencies: list[str] = []
    in_dependencies = False
    for line in text.splitlines():
        if re.match(r"^dependencies:\s*$", line):
            in_dependencies = True
            continue
        if in_dependencies and re.match(r"^[A-Za-z_][\w-]*:\s*", line):
            break
        if in_dependencies:
            match = re.match(r"^\s{2}([A-Za-z_][\w-]*):", line)
            if match and match.group(1) != "flutter":
                dependencies.append(match.group(1))
    result["dependencies"] = sorted(set(dependencies))
    return result


def find_files(root: Path, filename: str) -> list[Path]:
    matches: list[Path] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        if filename in files:
            matches.append(Path(current) / filename)
    return sorted(matches)


def parse_ios(root: Path) -> dict[str, object]:
    info_plists: list[dict[str, object]] = []
    for path in find_files(root / "ios", "Info.plist") if (root / "ios").is_dir() else []:
        try:
            payload = plistlib.loads(path.read_bytes())
        except Exception as error:  # malformed or templated plist
            info_plists.append({"path": str(path), "error": str(error)})
            continue
        usage = {key: value for key, value in payload.items() if key.startswith("NS") and key.endswith("UsageDescription")}
        info_plists.append(
            {
                "path": str(path),
                "display_name": payload.get("CFBundleDisplayName") or payload.get("CFBundleName"),
                "usage_descriptions": usage,
            }
        )

    project_files = (
        sorted(path for path in (root / "ios").rglob("project.pbxproj") if "Pods" not in path.parts)
        if (root / "ios").is_dir()
        else []
    )
    bundle_ids: set[str] = set()
    targeted_device_families: set[str] = set()
    for path in project_files:
        text = read_text(path)
        bundle_ids.update(value.strip().strip('"') for value in re.findall(r"PRODUCT_BUNDLE_IDENTIFIER\s*=\s*([^;]+);", text))
        targeted_device_families.update(value.strip().strip('"') for value in re.findall(r"TARGETED_DEVICE_FAMILY\s*=\s*([^;]+);", text))

    privacy_manifests: list[dict[str, object]] = []
    for path in find_files(root / "ios", "PrivacyInfo.xcprivacy") if (root / "ios").is_dir() else []:
        try:
            payload = plistlib.loads(path.read_bytes())
            privacy_manifests.append({"path": str(path), "payload": payload})
        except Exception as error:
            privacy_manifests.append({"path": str(path), "error": str(error)})

    return {
        "info_plists": info_plists,
        "bundle_identifiers": sorted(bundle_ids),
        "targeted_device_families": sorted(targeted_device_families),
        "privacy_manifests": privacy_manifests,
    }


def parse_android(root: Path) -> dict[str, object]:
    manifests = find_files(root / "android", "AndroidManifest.xml") if (root / "android").is_dir() else []
    records: list[dict[str, object]] = []
    android_ns = "{http://schemas.android.com/apk/res/android}"
    for path in manifests:
        try:
            tree = ET.parse(path)
            document = tree.getroot()
            permissions = sorted(
                {
                    node.attrib.get(android_ns + "name", "")
                    for node in document.findall("uses-permission")
                    if node.attrib.get(android_ns + "name")
                }
            )
            application = document.find("application")
            records.append(
                {
                    "path": str(path),
                    "package": document.attrib.get("package"),
                    "application_label": application.attrib.get(android_ns + "label") if application is not None else None,
                    "permissions": permissions,
                }
            )
        except Exception as error:
            records.append({"path": str(path), "error": str(error)})
    return {"manifests": records}


def scan_source(root: Path) -> tuple[list[str], list[dict[str, str]]]:
    hosts: set[str] = set()
    url_evidence: list[dict[str, str]] = []
    runtime_roots = [
        root / "lib",
        root / "assets",
        root / "content",
        root / "ios" / "Runner",
        root / "android" / "app" / "src" / "main",
        root / "packages",
    ]
    ignored_hosts = {
        "schemas.android.com",
        "www.apple.com",
        "developer.apple.com",
        "developer.android.com",
        "dart.dev",
        "flutter.dev",
    }
    for scan_root in (path for path in runtime_roots if path.is_dir()):
        for current, dirs, files in os.walk(scan_root):
            dirs[:] = [name for name in dirs if name not in IGNORED_DIRS and not name.startswith(".")]
            current_path = Path(current)
            for name in files:
                path = current_path / name
                if path.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                text = read_text(path)
                for match in URL_PATTERN.findall(text):
                    cleaned = match.rstrip(".,;:")
                    host = urlparse(cleaned).hostname
                    if host and host.lower() not in ignored_hosts:
                        hosts.add(host.lower())
                        if len(url_evidence) < 100:
                            url_evidence.append({"host": host.lower(), "path": str(path.relative_to(root))})
    unique_evidence = {(item["host"], item["path"]): item for item in url_evidence}
    return sorted(hosts), [unique_evidence[key] for key in sorted(unique_evidence)]


def dependency_signals(dependencies: list[str]) -> dict[str, list[str]]:
    lowered = {dependency: dependency.lower() for dependency in dependencies}
    result: dict[str, list[str]] = {}
    for group, needles in SIGNAL_GROUPS.items():
        hits = sorted(
            dependency
            for dependency, normalized in lowered.items()
            if any(needle in normalized for needle in needles)
        )
        if hits:
            result[group] = hits
    return result


def collect(root: Path) -> dict[str, object]:
    pubspec = parse_pubspec(root)
    hosts, url_evidence = scan_source(root)
    dependencies = list(pubspec.get("dependencies") or [])
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "app_root": str(root),
        "warning": "These are source signals, not verified privacy or product conclusions.",
        "pubspec": pubspec,
        "ios": parse_ios(root),
        "android": parse_android(root),
        "network_hosts_observed": hosts,
        "network_host_evidence": url_evidence,
        "dependency_signals": dependency_signals(dependencies),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app_root", type=Path)
    parser.add_argument("--output", type=str, default="-", help="JSON path, or - for stdout")
    args = parser.parse_args()

    root = find_app_root(args.app_root)
    rendered = json.dumps(collect(root), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        sys.stdout.write(rendered)
        return
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered)
    print(destination)


if __name__ == "__main__":
    main()

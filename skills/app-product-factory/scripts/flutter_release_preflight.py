#!/usr/bin/env python3
"""Collect mechanical Flutter/iOS release evidence without uploading anything."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from typing import Any, Iterable
from urllib.parse import urlparse


PLACEHOLDER_BUNDLE = re.compile(
    r"(^|\.)(example|sample|placeholder|yourcompany|company)(\.|$)", re.IGNORECASE
)
PREVIEW_WORDS = re.compile(r"\b(mvp|prototype|demo app)\b|演示版|原型版", re.IGNORECASE)
SOURCE_SUFFIXES = {
    ".arb",
    ".dart",
    ".java",
    ".json",
    ".kt",
    ".m",
    ".mm",
    ".plist",
    ".strings",
    ".swift",
    ".txt",
    ".xcstrings",
    ".xml",
    ".yaml",
    ".yml",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect release inputs, an optional iOS archive, screenshots, and artifacts."
    )
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument(
        "--archive",
        type=Path,
        help="Defaults to build/ios/archive/Runner.xcarchive when present.",
    )
    parser.add_argument("--privacy-url")
    parser.add_argument("--support-url")
    parser.add_argument(
        "--expected-bundle-id",
        help="Required when the project has multiple production Bundle IDs or flavors.",
    )
    parser.add_argument(
        "--expected-version",
        help="Expected CFBundleShortVersionString; defaults to pubspec.yaml version when available.",
    )
    parser.add_argument(
        "--expected-build-number",
        help="Expected CFBundleVersion; defaults to pubspec.yaml build number when available.",
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        action="append",
        default=[],
        help="Repeat for each candidate App Store screenshot.",
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        action="append",
        default=[],
        help="Repeat for files that should receive SHA-256 evidence.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Defaults to docs/release/evidence/automation in the project.",
    )
    parser.add_argument("--fail-on-warning", action="store_true")
    return parser.parse_args()


def add_check(
    checks: list[dict[str, Any]],
    key: str,
    status: str,
    summary: str,
    evidence: Any = None,
    limitation: str | None = None,
) -> None:
    checks.append(
        {
            "key": key,
            "status": status,
            "summary": summary,
            "evidence": evidence,
            "limitation": limitation,
        }
    )


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as error:
        return subprocess.CompletedProcess(command, 127, str(error))


def git_facts(project: Path) -> dict[str, Any]:
    root = run(["git", "rev-parse", "--show-toplevel"], project)
    if root.returncode != 0:
        return {"is_repository": False}
    branch = run(["git", "branch", "--show-current"], project)
    sha = run(["git", "rev-parse", "HEAD"], project)
    status = run(["git", "status", "--short"], project)
    return {
        "is_repository": True,
        "root": root.stdout.strip(),
        "branch": branch.stdout.strip() if branch.returncode == 0 else None,
        "sha": sha.stdout.strip() if sha.returncode == 0 else None,
        "dirty": bool(status.stdout.strip()),
        "status_short": status.stdout.strip(),
    }


def bundle_identifiers(project: Path) -> list[str]:
    project_file = project / "ios" / "Runner.xcodeproj" / "project.pbxproj"
    if not project_file.is_file():
        return []
    text = project_file.read_text(encoding="utf-8", errors="replace")
    values = re.findall(r"PRODUCT_BUNDLE_IDENTIFIER\s*=\s*([^;]+);", text)
    return sorted(
        {
            value.strip().strip('"')
            for value in values
            if "$" not in value and value.strip()
        }
    )


def flutter_version_facts(project: Path) -> dict[str, str | None]:
    pubspec = project / "pubspec.yaml"
    text = pubspec.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^version:\s*['\"]?([^+\s'\"]+)(?:\+([^\s#'\"]+))?", text, re.MULTILINE)
    if not match:
        return {"version": None, "build_number": None}
    return {"version": match.group(1), "build_number": match.group(2)}


def valid_public_https(value: str | None) -> tuple[bool, str]:
    if not value:
        return False, "not provided"
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    invalid_hosts = {"localhost", "127.0.0.1", "::1"}
    documentation_domains = ("example.com", "example.net", "example.org")
    reserved_suffixes = (".example", ".invalid", ".localhost", ".local", ".test")
    if (
        parsed.scheme != "https"
        or not host
        or host in invalid_hosts
        or any(host == domain or host.endswith(f".{domain}") for domain in documentation_domains)
        or host.endswith(reserved_suffixes)
        or parsed.username is not None
        or parsed.password is not None
    ):
        return False, "must be a non-placeholder public HTTPS URL"
    return True, "syntax accepted; live availability and content were not checked"


def create_unique_run_dir(output_dir: Path, run_id: str) -> Path:
    """Create a run directory without overwriting evidence from a concurrent run."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for sequence in range(100):
        suffix = "" if sequence == 0 else f"-{sequence:02d}"
        candidate = output_dir / f"preflight-{run_id}{suffix}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError(f"Could not allocate a unique evidence directory in {output_dir}")


def png_facts(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    color_type = data[25]
    has_alpha = color_type in {4, 6} or b"tRNS" in data
    return {"width": width, "height": height, "has_alpha": has_alpha}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_facts(path: Path) -> dict[str, Any]:
    stat = path.stat()
    result: dict[str, Any] = {
        "path": str(path),
        "size_bytes": stat.st_size,
        "modified_at": dt.datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
    }
    if path.is_file():
        result["sha256"] = sha256(path)
    else:
        result["note"] = "directory contents were not hashed"
    return result


def candidate_source_files(project: Path) -> Iterable[Path]:
    roots = [project / "lib", project / "ios" / "Runner", project / "android" / "app" / "src" / "main"]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in SOURCE_SUFFIXES and path.stat().st_size <= 1_000_000:
                yield path


def preview_word_hits(project: Path) -> list[str]:
    hits: list[str] = []
    for path in candidate_source_files(project):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if PREVIEW_WORDS.search(line):
                hits.append(f"{path.relative_to(project)}:{line_number}")
                if len(hits) >= 50:
                    return hits
    return hits


def inspect_archive(
    project: Path, archive: Path, checks: list[dict[str, Any]]
) -> dict[str, Any]:
    facts: dict[str, Any] = {"path": str(archive), "exists": archive.exists()}
    if not archive.is_dir():
        add_check(
            checks,
            "ios_archive",
            "blocker",
            "No iOS archive was available for inspection.",
            str(archive),
        )
        return facts

    applications = sorted((archive / "Products" / "Applications").glob("*.app"))
    if len(applications) != 1:
        add_check(
            checks,
            "ios_archive_app",
            "blocker",
            "Expected exactly one .app in the archive.",
            [str(path) for path in applications],
        )
        return facts

    app = applications[0]
    facts["app"] = str(app)
    info_path = app / "Info.plist"
    if info_path.is_file():
        try:
            with info_path.open("rb") as stream:
                info = plistlib.load(stream)
            facts["info"] = {
                key: info.get(key)
                for key in (
                    "CFBundleIdentifier",
                    "CFBundleShortVersionString",
                    "CFBundleVersion",
                    "MinimumOSVersion",
                    "DTXcode",
                    "DTSDKName",
                    "CFBundleDevelopmentRegion",
                )
            }
            add_check(
                checks,
                "archive_info",
                "pass",
                "Archive Info.plist was parsed.",
                facts["info"],
            )
        except (OSError, plistlib.InvalidFileException) as error:
            add_check(checks, "archive_info", "blocker", f"Invalid archive Info.plist: {error}")
    else:
        add_check(checks, "archive_info", "blocker", "Archive app is missing Info.plist.")

    verify = run(["codesign", "--verify", "--deep", "--strict", str(app)], project)
    details = run(["codesign", "-dv", "--verbose=4", str(app)], project)
    provisioning = app / "embedded.mobileprovision"
    signing_evidence = {
        "verify_return_code": verify.returncode,
        "verify_output": verify.stdout.strip()[:2000],
        "details": details.stdout.strip()[:4000],
        "embedded_mobileprovision": provisioning.is_file(),
    }
    signed = verify.returncode == 0 and details.returncode == 0 and provisioning.is_file()
    add_check(
        checks,
        "code_signing_presence",
        "pass" if signed else "blocker",
        "Archive signature validates and an embedded provisioning profile exists."
        if signed
        else "Archive lacks a validating signature or embedded provisioning profile.",
        signing_evidence,
        "This does not identify the profile as App Store distribution, validate its entitlements or expiry, or prove App Store Connect acceptance.",
    )

    manifests = sorted(app.rglob("PrivacyInfo.xcprivacy"))
    manifest_results = []
    for manifest in manifests:
        try:
            with manifest.open("rb") as stream:
                plistlib.load(stream)
            manifest_results.append({"path": str(manifest.relative_to(app)), "valid_plist": True})
        except (OSError, plistlib.InvalidFileException):
            manifest_results.append({"path": str(manifest.relative_to(app)), "valid_plist": False})
    manifest_ok = bool(manifest_results) and all(item["valid_plist"] for item in manifest_results)
    add_check(
        checks,
        "privacy_manifests",
        "pass" if manifest_ok else "warning",
        "Privacy manifests were found and parsed."
        if manifest_ok
        else "Privacy manifests are missing or at least one is invalid.",
        manifest_results,
        "Manifest presence does not replace a final Xcode Privacy Report or App Store privacy answers.",
    )

    frameworks_dir = app / "Frameworks"
    frameworks = sorted(path.name for path in frameworks_dir.iterdir()) if frameworks_dir.is_dir() else []
    facts["frameworks"] = frameworks
    add_check(
        checks,
        "archive_dependencies",
        "info",
        "Recorded embedded archive frameworks for reviewer inspection.",
        frameworks,
        "This is a package inventory, not network or SDK-behavior proof.",
    )
    return facts


def markdown_report(report: dict[str, Any]) -> str:
    rows = []
    for check in report["checks"]:
        evidence = check.get("evidence")
        if isinstance(evidence, (dict, list)):
            evidence_text = json.dumps(evidence, ensure_ascii=False)
        else:
            evidence_text = str(evidence or "")
        evidence_text = evidence_text.replace("|", "\\|").replace("\n", " ")[:600]
        rows.append(
            f"| `{check['status']}` | {check['key']} | {check['summary']} | {evidence_text} |"
        )
    artifacts = [
        f"- `{item['path']}` — SHA-256 `{item.get('sha256', '[directory not hashed]')}`, "
        f"{item['size_bytes']} bytes"
        for item in report["artifacts"]
    ]
    if not artifacts:
        artifacts = ["- No file artifacts were supplied or discovered for hashing."]
    return "\n".join(
        [
            "# Flutter Release Mechanical Preflight",
            "",
            f"Generated: {report['generated_at']}",
            f"Project: `{report['project']}`",
            f"Mechanical verdict: `{report['verdict']}`",
            "",
            "| Status | Check | Summary | Evidence |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## Artifact hashes",
            "",
            *artifacts,
            "",
            "## Required interpretation",
            "",
            "- `review_required` is not an App Store candidate verdict; the Store Reviewer must verify current official requirements and external state.",
            "- This script does not check trademark rights, legal sufficiency, real URL content, App Store Connect metadata, physical devices, upload processing, TestFlight, or App Review.",
            "- This script never uploads, submits, changes certificates, or mutates external accounts.",
            "",
        ]
    )


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    args = parse_args()
    project = args.project.expanduser().resolve()
    if not (project / "pubspec.yaml").is_file():
        print(f"Not a Flutter project: {project}", file=sys.stderr)
        return 2

    now = dt.datetime.now(dt.timezone.utc).astimezone()
    run_id = now.strftime("%Y%m%dT%H%M%S%z")
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else project / "docs" / "release" / "evidence" / "automation"
    )
    report_dir = create_unique_run_dir(output_dir, run_id)
    checks: list[dict[str, Any]] = []

    git = git_facts(project)
    add_check(
        checks,
        "source_traceability",
        "pass" if git.get("is_repository") and git.get("sha") else "warning",
        "Git source identity is available."
        if git.get("is_repository") and git.get("sha")
        else "No commit-level Git identity is available.",
        git,
    )

    identifiers = bundle_identifiers(project)
    production_identifiers = [value for value in identifiers if not value.lower().endswith("runnertests")]
    placeholders = [value for value in production_identifiers if PLACEHOLDER_BUNDLE.search(value)]
    expected_bundle = args.expected_bundle_id.strip() if args.expected_bundle_id else None
    identity_ok = (
        bool(expected_bundle)
        and expected_bundle in production_identifiers
        and not PLACEHOLDER_BUNDLE.search(expected_bundle)
    ) or (
        expected_bundle is None
        and len(production_identifiers) == 1
        and not placeholders
    )
    if expected_bundle is None and len(production_identifiers) > 1:
        identity_summary = "Multiple production Bundle IDs found; pass --expected-bundle-id for the intended flavor."
    elif expected_bundle and expected_bundle not in production_identifiers:
        identity_summary = "Expected Bundle ID is not present in the project configuration."
    elif identity_ok:
        identity_summary = "One unambiguous production-looking iOS Bundle ID was selected."
    else:
        identity_summary = "Missing or placeholder iOS Bundle ID."
    add_check(
        checks,
        "bundle_identity",
        "pass" if identity_ok else "blocker",
        identity_summary,
        {
            "identifiers": identifiers,
            "placeholders": placeholders,
            "expected_bundle_id": expected_bundle,
        },
        "Ownership and availability cannot be established from local configuration."
        if identity_ok
        else None,
    )

    for key, value in (("privacy_url", args.privacy_url), ("support_url", args.support_url)):
        valid, note = valid_public_https(value)
        add_check(
            checks,
            key,
            "warning" if valid else "blocker",
            f"{key.replace('_', ' ').title()}: {note}.",
            value,
            "The Store Reviewer must open the URL and compare its content with the final app and metadata."
            if valid
            else None,
        )

    word_hits = preview_word_hits(project)
    add_check(
        checks,
        "preview_labels",
        "warning" if word_hits else "pass",
        "Potential prototype/demo wording remains in app-facing source."
        if word_hits
        else "No common MVP/prototype/demo wording was found in the scanned app-facing source types.",
        {"hits": word_hits, "scanned_suffixes": sorted(SOURCE_SUFFIXES)},
        "This bounded source scan does not inspect remote content, generated store metadata, or every possible asset format.",
    )

    icon = project / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset" / "Icon-App-1024x1024@1x.png"
    try:
        icon_info = png_facts(icon)
        icon_ok = icon_info["width"] == 1024 and icon_info["height"] == 1024 and not icon_info["has_alpha"]
        add_check(
            checks,
            "app_icon",
            "pass" if icon_ok else "blocker",
            "1024px AppIcon exists without alpha."
            if icon_ok
            else "AppIcon must be a 1024x1024 PNG without alpha.",
            {"path": str(icon), **icon_info},
            "This does not establish originality, trademark clearance, or complete asset-catalog coverage.",
        )
    except (OSError, ValueError) as error:
        add_check(checks, "app_icon", "blocker", f"Cannot validate 1024px AppIcon: {error}", str(icon))

    archive = (
        args.archive.expanduser().resolve()
        if args.archive
        else project / "build" / "ios" / "archive" / "Runner.xcarchive"
    )
    archive_facts = inspect_archive(project, archive, checks)
    archive_info = archive_facts.get("info") or {}
    selected_bundle = expected_bundle or (
        production_identifiers[0] if len(production_identifiers) == 1 else None
    )
    archived_bundle = archive_info.get("CFBundleIdentifier")
    archive_identity_ok = bool(selected_bundle) and archived_bundle == selected_bundle
    add_check(
        checks,
        "archive_source_identity",
        "pass" if archive_identity_ok else "blocker",
        "Archive Bundle ID matches the selected source configuration."
        if archive_identity_ok
        else "Archive Bundle ID cannot be tied to the selected source configuration.",
        {"expected": selected_bundle, "archive": archived_bundle},
        "Bundle ID equality does not prove that the archive was built from the current commit."
        if archive_identity_ok
        else None,
    )

    pubspec_version = flutter_version_facts(project)
    expected_version = args.expected_version or pubspec_version["version"]
    expected_build = args.expected_build_number or pubspec_version["build_number"]
    archived_version = archive_info.get("CFBundleShortVersionString")
    archived_build = archive_info.get("CFBundleVersion")
    version_comparable = bool(expected_version and expected_build and archived_version and archived_build)
    version_matches = version_comparable and (
        str(archived_version) == str(expected_version)
        and str(archived_build) == str(expected_build)
    )
    add_check(
        checks,
        "archive_source_version",
        "pass" if version_matches else ("blocker" if version_comparable else "warning"),
        "Archive version and build number match the expected Flutter source values."
        if version_matches
        else (
            "Archive version or build number does not match the expected Flutter source values."
            if version_comparable
            else "Archive/source version relationship could not be fully evaluated."
        ),
        {
            "expected_version": expected_version,
            "expected_build_number": expected_build,
            "archive_version": archived_version,
            "archive_build_number": archived_build,
        },
    )

    screenshots = [path.expanduser().resolve() for path in args.screenshot]
    if not screenshots:
        screenshots = sorted((project / "docs" / "release" / "evidence").glob("**/*.png"))
    screenshot_facts: list[dict[str, Any]] = []
    invalid_screenshots: list[str] = []
    for screenshot in screenshots:
        try:
            info = png_facts(screenshot)
            screenshot_facts.append({"path": str(screenshot), **info})
            if info["has_alpha"]:
                invalid_screenshots.append(str(screenshot))
        except (OSError, ValueError):
            invalid_screenshots.append(str(screenshot))
    if not screenshot_facts:
        add_check(checks, "screenshots", "blocker", "No PNG runtime/store screenshot evidence was found.")
    else:
        add_check(
            checks,
            "screenshots",
            "warning" if invalid_screenshots else "pass",
            "Screenshots exist but at least one has alpha or is unreadable."
            if invalid_screenshots
            else "Screenshot PNG dimensions and alpha were inspected.",
            screenshot_facts,
            "Current App Store device classes, required counts, content, and final-build provenance still require live review.",
        )

    requested_artifacts = [path.expanduser().resolve() for path in args.artifact]
    missing_requested_artifacts = [str(path) for path in requested_artifacts if not path.exists()]
    if requested_artifacts:
        add_check(
            checks,
            "requested_artifacts",
            "blocker" if missing_requested_artifacts else "pass",
            "At least one explicitly requested artifact is missing."
            if missing_requested_artifacts
            else "All explicitly requested artifacts exist and will be recorded.",
            {
                "requested": [str(path) for path in requested_artifacts],
                "missing": missing_requested_artifacts,
            },
        )
    artifact_paths = list(requested_artifacts)
    default_apk = project / "build" / "app" / "outputs" / "flutter-apk" / "app-debug.apk"
    if default_apk.is_file() and default_apk not in artifact_paths:
        artifact_paths.append(default_apk)
    app_path = Path(archive_facts["app"]) if archive_facts.get("app") else None
    if app_path:
        executable_name = app_path.stem
        executable = app_path / executable_name
        if executable.is_file() and executable not in artifact_paths:
            artifact_paths.append(executable)
    for screenshot in screenshots:
        if screenshot.is_file() and screenshot not in artifact_paths:
            artifact_paths.append(screenshot)
    artifacts = [file_facts(path) for path in artifact_paths if path.exists()]

    has_blocker = any(check["status"] == "blocker" for check in checks)
    has_warning = any(check["status"] == "warning" for check in checks)
    verdict = "blocked" if has_blocker else "review_required"
    report = {
        "schema_version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "project": str(project),
        "verdict": verdict,
        "git": git,
        "archive": archive_facts,
        "checks": checks,
        "artifacts": artifacts,
    }
    json_path = report_dir / "release-preflight.json"
    markdown_path = report_dir / "RELEASE_PREFLIGHT.md"
    atomic_write(json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    atomic_write(markdown_path, markdown_report(report))
    print(f"{verdict.upper()}: {markdown_path}")
    print(f"JSON: {json_path}")
    if has_blocker or (args.fail_on_warning and has_warning):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

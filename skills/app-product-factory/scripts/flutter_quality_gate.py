#!/usr/bin/env python3
"""Run repeatable, non-uploading Flutter quality gates and record evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any, Sequence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Flutter format/analyze/test and optional local builds."
    )
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument(
        "--flutter-command",
        help="Flutter command override, for example 'fvm flutter'.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Defaults to docs/release/evidence/automation in the project.",
    )
    parser.add_argument("--android-debug", action="store_true")
    parser.add_argument("--ios-no-codesign", action="store_true")
    parser.add_argument(
        "--flavor",
        help="Flutter flavor for requested builds; inspect the project before choosing it.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        help="Project-relative Dart entry point for requested builds, such as lib/main_prod.dart.",
    )
    parser.add_argument(
        "--all-local",
        action="store_true",
        help="Also build Android debug and, on macOS, an unsigned iOS archive.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=1800,
        help="Per-command timeout; default 1800 seconds.",
    )
    return parser.parse_args()


def resolve_flutter(project: Path, override: str | None) -> list[str]:
    if override:
        command = shlex.split(override)
        if not command:
            raise ValueError("--flutter-command cannot be empty")
        return command

    local_flutter = project / ".fvm" / "flutter_sdk" / "bin" / "flutter"
    if local_flutter.is_file():
        return [str(local_flutter)]
    if (project / ".fvmrc").is_file() and shutil.which("fvm"):
        return ["fvm", "flutter"]
    flutter = shutil.which("flutter")
    if not flutter:
        raise ValueError("Flutter was not found. Pass --flutter-command explicitly.")
    return [flutter]


def resolve_dart(flutter: Sequence[str]) -> list[str]:
    if len(flutter) == 1:
        sibling = Path(flutter[0]).resolve().with_name("dart")
        if sibling.is_file():
            return [str(sibling)]
    if list(flutter[:2]) == ["fvm", "flutter"]:
        return ["fvm", "dart"]
    dart = shutil.which("dart")
    if not dart:
        raise ValueError("Dart was not found next to Flutter or on PATH.")
    return [dart]


def git_facts(project: Path) -> dict[str, Any]:
    def capture(args: list[str]) -> str | None:
        result = subprocess.run(
            args,
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None

    root = capture(["git", "rev-parse", "--show-toplevel"])
    if root is None:
        return {"is_repository": False}
    status = capture(["git", "status", "--short"])
    return {
        "is_repository": True,
        "root": root,
        "branch": capture(["git", "branch", "--show-current"]),
        "sha": capture(["git", "rev-parse", "HEAD"]),
        "dirty": bool(status),
        "status_short": status or "",
    }


def command_version(command: list[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = result.stdout.strip()
    return text if result.returncode == 0 and text else None


def create_unique_run_dir(output_dir: Path, run_id: str) -> Path:
    """Create a run directory without overwriting evidence from a concurrent run."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for sequence in range(100):
        suffix = "" if sequence == 0 else f"-{sequence:02d}"
        candidate = output_dir / f"{run_id}{suffix}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError(f"Could not allocate a unique evidence directory in {output_dir}")


def concise_result(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return "No command output"
    return lines[-1][:500]


def report_path(path: Path, project: Path) -> str:
    try:
        return str(path.relative_to(project))
    except ValueError:
        return str(path)


def run_step(
    name: str,
    command: list[str],
    project: Path,
    logs_dir: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    safe_name = name.replace(" ", "-").replace("/", "-")
    log_path = logs_dir / f"{safe_name}.log"
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout_seconds,
            env=os.environ.copy(),
        )
        status = "passed" if result.returncode == 0 else "failed"
        return_code: int | None = result.returncode
        output = result.stdout
    except subprocess.TimeoutExpired as error:
        status = "timed_out"
        return_code = None
        captured = error.stdout or ""
        output = captured if isinstance(captured, str) else captured.decode(errors="replace")
        output += f"\nTimed out after {timeout_seconds} seconds.\n"
    except OSError as error:
        status = "failed_to_start"
        return_code = None
        output = f"{error}\n"

    duration = round(time.monotonic() - started, 3)
    log_path.write_text(output, encoding="utf-8")
    return {
        "name": name,
        "command": command,
        "status": status,
        "return_code": return_code,
        "duration_seconds": duration,
        "summary": concise_result(output),
        "log": report_path(log_path, project),
    }


def markdown_report(report: dict[str, Any]) -> str:
    rows = []
    for step in report["steps"]:
        command = " ".join(shlex.quote(part) for part in step["command"])
        rows.append(
            f"| {step['name']} | `{step['status']}` | `{command}` | "
            f"{step['duration_seconds']}s | `{step['log']}` |"
        )
    git = report["git"]
    git_line = "not a Git repository"
    if git.get("is_repository"):
        git_line = (
            f"branch `{git.get('branch') or '[detached]'}`, SHA `{git.get('sha')}`, "
            f"dirty `{str(git.get('dirty')).lower()}`"
        )
    return "\n".join(
        [
            "# Flutter Quality Gate",
            "",
            f"Generated: {report['generated_at']}",
            f"Project: `{report['project']}`",
            f"Verdict: `{report['verdict']}`",
            f"Git: {git_line}",
            "",
            "| Step | Status | Command | Duration | Full log |",
            "| --- | --- | --- | ---: | --- |",
            *rows,
            "",
            "## Evidence limits",
            "",
            "- Formatting, analyzer, and automated tests do not prove simulator or physical-device behavior.",
            "- An Android debug APK is not a Play release artifact; Gradle may create or use a local debug keystore for that explicitly requested build.",
            "- An unsigned iOS archive does not prove signing, installation, upload, TestFlight, or App Review.",
            "- This script never performs production signing, changes production certificates/accounts, uploads, or submits; an explicitly requested Android debug build may create or use a local debug keystore.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    project = args.project.expanduser().resolve()
    if not (project / "pubspec.yaml").is_file():
        print(f"Not a Flutter project: {project}", file=sys.stderr)
        return 2
    if args.timeout_seconds <= 0:
        print("--timeout-seconds must be positive", file=sys.stderr)
        return 2

    try:
        flutter = resolve_flutter(project, args.flutter_command)
        dart = resolve_dart(flutter)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    target_argument: str | None = None
    if args.target:
        target = (
            args.target.expanduser().resolve()
            if args.target.is_absolute()
            else (project / args.target).resolve()
        )
        try:
            target_argument = str(target.relative_to(project))
        except ValueError:
            print("--target must resolve inside the Flutter project.", file=sys.stderr)
            return 2
        if not target.is_file() or target.suffix != ".dart":
            print(f"Flutter build target is not a Dart file: {target}", file=sys.stderr)
            return 2

    build_ios = args.ios_no_codesign or (args.all_local and platform.system() == "Darwin")
    if build_ios and platform.system() != "Darwin":
        print("Unsigned iOS archive requires macOS.", file=sys.stderr)
        return 2

    now = dt.datetime.now(dt.timezone.utc).astimezone()
    run_id = now.strftime("%Y%m%dT%H%M%S%z")
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else project / "docs" / "release" / "evidence" / "automation"
    )
    logs_dir = create_unique_run_dir(output_dir, run_id)

    format_targets = [name for name in ("lib", "test") if (project / name).exists()]
    steps: list[tuple[str, list[str]]] = []
    if format_targets:
        steps.append(
            (
                "format-check",
                [*dart, "format", "--output=none", "--set-exit-if-changed", *format_targets],
            )
        )
    steps.extend(
        [
            ("flutter-analyze", [*flutter, "analyze", "--no-pub"]),
            (
                "flutter-test",
                [*flutter, "test", "--no-pub", "--reporter", "expanded"],
            ),
        ]
    )

    build_android = args.android_debug or args.all_local
    build_options: list[str] = []
    if args.flavor:
        build_options.extend(["--flavor", args.flavor])
    if target_argument:
        build_options.extend(["--target", target_argument])
    if build_android:
        steps.append(
            (
                "android-debug-build",
                [*flutter, "build", "apk", "--debug", "--no-pub", *build_options],
            )
        )
    if build_ios:
        steps.append(
            (
                "ios-unsigned-archive",
                [
                    *flutter,
                    "build",
                    "ipa",
                    "--release",
                    "--no-codesign",
                    "--no-pub",
                    *build_options,
                ],
            )
        )

    results = [
        run_step(name, command, project, logs_dir, args.timeout_seconds)
        for name, command in steps
    ]
    verdict = "passed" if all(item["status"] == "passed" for item in results) else "failed"
    report = {
        "schema_version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "project": str(project),
        "verdict": verdict,
        "git": git_facts(project),
        "environment": {
            "platform": platform.platform(),
            "flutter_command": flutter,
            "flutter_version": command_version([*flutter, "--version"], project),
            "dart_version": command_version([*dart, "--version"], project),
            "xcode_version": command_version(["xcodebuild", "-version"], project)
            if platform.system() == "Darwin"
            else None,
        },
        "build_configuration": {
            "flavor": args.flavor,
            "target": target_argument,
            "android_debug_signing_note": (
                "An explicitly requested Android debug build may create or use a local debug keystore."
                if build_android
                else None
            ),
        },
        "steps": results,
    }

    json_path = logs_dir / "quality-gate.json"
    markdown_path = logs_dir / "QUALITY_GATE.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    print(f"{verdict.upper()}: {markdown_path}")
    print(f"JSON: {json_path}")
    return 0 if verdict == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

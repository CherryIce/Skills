#!/usr/bin/env python3
"""Preview or remove explicitly selected, project-local disposable build trees."""

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys


class Refused(ValueError):
    pass


PROTECTED = {
    ".git", ".fvm", ".pub-cache", ".venv", "venv", "Pods", "vendor",
    ".swiftpm", "outputs", "artifacts", "releases", "node_modules",
}
SIGNING_SUFFIXES = {".p12", ".pfx", ".jks", ".keystore", ".mobileprovision"}


def literal_path(value):
    path = Path(value).expanduser()
    if not path.is_absolute() or ".." in path.parts or any(c in value for c in "*?[]\x00"):
        raise Refused("use an absolute literal path without traversal or wildcards")
    return path


def inside(path, parent):
    return path == parent or parent in path.parents


def overlaps(left, right):
    return inside(left, right) or inside(right, left)


def allowed(relative):
    parts = relative.parts
    for index, part in enumerate(parts):
        if part in {".codex-build", "build", "target", ".build", ".gradle", ".derivedData"}:
            return True
        if part.startswith("DerivedData") or part.startswith("cmake-build-"):
            return True
        if index + 1 < len(parts) and (part, parts[index + 1]) in {
            (".dart_tool", "flutter_build"), (".next", "cache"), ("node_modules", ".cache"),
        }:
            return True
    return False


def git_tracked_files(project, target):
    probe = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
        capture_output=True,
    )
    if probe.returncode:
        # An ordinary non-Git directory is supported; other Git failures fail closed.
        if b"not a git repository" in probe.stderr:
            return
        raise Refused("cannot verify Git ownership: " + os.fsdecode(probe.stderr).strip())
    repo = Path(os.fsdecode(probe.stdout).strip()).resolve()
    if not inside(target, repo):
        raise Refused("target is outside the detected Git repository")
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--cached", "-z", "--",
         ":(literal)" + target.relative_to(repo).as_posix()],
        capture_output=True,
    )
    if result.returncode:
        raise Refused("cannot inspect tracked files")
    if result.stdout:
        first = os.fsdecode(result.stdout.split(b"\0")[0])
        raise Refused("contains a tracked file or submodule: " + first)


def scan_tree(target):
    total = 0
    base_device = target.stat().st_dev

    def walk_error(error):
        raise error

    for directory, dirs, files in os.walk(target, followlinks=False, onerror=walk_error):
        current = Path(directory)
        entries = [(current, False)] + [(current / name, True) for name in dirs + files]
        for entry, is_child in entries:
            if is_child and entry.name in PROTECTED:
                raise Refused("contains protected data: " + str(entry))
            if entry.suffix.lower() in SIGNING_SUFFIXES:
                raise Refused("contains signing material: " + str(entry))
            info = entry.lstat()
            if info.st_dev != base_device or (is_child and os.path.ismount(entry)):
                raise Refused("contains a different filesystem or mount: " + str(entry))
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
                raise Refused("contains a non-regular filesystem entry: " + str(entry))
            # Count directories on their own visit; symbolic links are never followed.
            if not is_child or not stat.S_ISDIR(info.st_mode):
                total += getattr(info, "st_blocks", 0) * 512
    return total


def inspect(project, raw_target, keep):
    target = literal_path(raw_target)
    if not inside(target, project) or target == project:
        raise Refused("target must be strictly inside the project")
    relative = target.relative_to(project)
    parts = relative.parts
    for index, part in enumerate(parts):
        node_cache = part == "node_modules" and index + 1 < len(parts) and parts[index + 1] == ".cache"
        if part in PROTECTED and not node_cache:
            raise Refused("protected path component: " + part)
    if not allowed(relative):
        raise Refused("not a recognized build/cache path; use a dedicated .codex-build output")
    for segment in [target, *target.parents]:
        if segment == project:
            break
        if segment.is_symlink():
            raise Refused("target or ancestor is a symbolic link: " + str(segment))
    resolved = target.resolve()
    if any(overlaps(resolved, item) for item in keep):
        raise Refused("overlaps a --keep path")
    if not target.exists():
        return {"path": str(target), "status": "already_absent", "estimated_bytes": 0}
    if not target.is_dir() or os.path.ismount(target):
        raise Refused("target must be a regular directory, not a mount")
    git_tracked_files(project, target)
    return {"path": str(target), "status": "eligible", "estimated_bytes": scan_tree(target)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="absolute application root")
    parser.add_argument("--cache", action="append", required=True, help="exact disposable directory; repeatable")
    parser.add_argument("--keep", action="append", default=[], help="protected artifact/evidence path; repeatable")
    parser.add_argument("--apply", action="store_true", help="delete after all targets pass preflight")
    args = parser.parse_args(argv)
    report = {"mode": "apply" if args.apply else "preview", "targets": [], "errors": []}
    try:
        project = literal_path(args.project).resolve(strict=True)
        if not project.is_dir() or project in {Path("/"), Path.home(), Path.home() / ".codex", Path.home() / ".agents"}:
            raise Refused("project must be a specific application directory")
        # Protect both a kept link's location and the object it references.
        keep = []
        for item in args.keep:
            path = literal_path(item)
            keep.extend([path, path.resolve()])
        candidates = list(dict.fromkeys(args.cache))
        for candidate in candidates:
            try:
                report["targets"].append(inspect(project, candidate, keep))
            except (OSError, ValueError) as error:
                report["errors"].append({"path": candidate, "reason": str(error)})
        paths = [Path(item["path"]) for item in report["targets"]]
        if any(overlaps(a, b) for index, a in enumerate(paths) for b in paths[index + 1:]):
            raise Refused("overlapping targets; select either the parent or its children")
    except (OSError, ValueError) as error:
        report["errors"].append({"reason": str(error)})
    if report["errors"]:
        report["status"] = "refused_no_deletion"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    for item in report["targets"]:
        if args.apply and item["status"] == "eligible":
            try:
                # Recheck immediately before deletion; callers must ensure exclusive use.
                inspect(project, item["path"], keep)
                shutil.rmtree(item["path"])
                if os.path.lexists(item["path"]):
                    raise OSError("directory remains or was recreated; it may still be in use")
                item["status"] = "removed"
            except (OSError, ValueError) as error:
                item["status"] = "failed_or_partial"
                report["errors"].append({"path": item["path"], "reason": str(error)})
                break
    report["estimated_removed_bytes"] = sum(
        item["estimated_bytes"] for item in report["targets"] if item["status"] == "removed"
    )
    report["status"] = "partial_failure" if report["errors"] else "complete"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

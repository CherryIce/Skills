#!/usr/bin/env python3
"""Exercise deletion boundaries using only disposable local fixture projects."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("cleanup_build_data.py")


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cleanup-test-", dir=Path.cwd())
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / "project with spaces"
        self.project.mkdir()
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)

    def file(self, relative, data="fixture"):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
        return path

    def run_cleanup(self, *targets, apply=False, keep=()):
        command = [sys.executable, str(SCRIPT), "--project", str(self.project)]
        for target in targets:
            command.extend(["--cache", str(target)])
        for item in keep:
            command.extend(["--keep", str(item)])
        if apply:
            command.append("--apply")
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def assert_refused(self, *targets, keep=()):
        code, report = self.run_cleanup(*targets, apply=True, keep=keep)
        self.assertEqual(code, 2, report)
        self.assertEqual(report["status"], "refused_no_deletion")

    def test_preview_does_not_delete(self):
        obj = self.file("build/obj.o", "x" * 8192)
        code, report = self.run_cleanup(obj.parent)
        self.assertEqual(code, 0, report)
        self.assertTrue(obj.exists())
        self.assertEqual(report["estimated_removed_bytes"], 0)

    def test_apply_preserves_source_deliverables_dependencies_and_sibling_app(self):
        obj = self.file("build/obj.o")
        generated = self.file(".dart_tool/flutter_build/snapshot")
        preserved = [self.file(name) for name in [
            "lib/main.dart", ".dart_tool/package_config.json", "outputs/app.ipa",
            "Pods/Manifest.lock", "other-app/build/other.o", "pubspec.lock",
        ]]
        code, report = self.run_cleanup(obj.parent, generated.parent, apply=True)
        self.assertEqual(code, 0, report)
        self.assertFalse(obj.exists())
        self.assertFalse(generated.exists())
        self.assertTrue(all(path.exists() for path in preserved))
        self.assertTrue(all(item["status"] == "removed" for item in report["targets"]))

    def test_supported_cache_directories(self):
        for relative in [".codex-build", "DerivedData-test", ".derivedData",
                         "android/app/build", ".gradle", ".next/cache",
                         "node_modules/.cache", "target/debug", ".build/debug",
                         "cmake-build-debug"]:
            with self.subTest(relative=relative):
                obj = self.file(relative + "/object.bin")
                code, report = self.run_cleanup(obj.parent, apply=True)
                self.assertEqual(code, 0, report)
                self.assertFalse(obj.exists())

    def test_missing_directory_is_idempotent(self):
        code, report = self.run_cleanup(self.project / "build", apply=True)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["targets"][0]["status"], "already_absent")

    def test_project_root_outside_and_source_are_refused(self):
        for target in [self.project, self.base / "build", self.file("src/main.swift").parent]:
            with self.subTest(target=target):
                self.assert_refused(target)

    def test_dependency_paths_are_refused(self):
        for relative in [".fvm/sdk/build", "Pods/SomePod/build", "node_modules/package/build",
                         "outputs/build", ".venv/build"]:
            with self.subTest(relative=relative):
                obj = self.file(relative + "/protected.bin")
                self.assert_refused(obj.parent)
                self.assertTrue(obj.exists())

    def test_kept_child_or_ancestor_blocks_removal(self):
        artifact = self.file("build/release/app.aab")
        self.assert_refused(self.project / "build", keep=[artifact])
        self.assert_refused(artifact.parent, keep=[self.project / "build"])
        self.assertTrue(artifact.exists())

    def test_link_target_and_link_ancestor_are_refused(self):
        outside = self.base / "outside"
        outside.mkdir()
        outside_file = outside / "app.bin"
        outside_file.write_text("keep")
        link = self.project / "build"
        link.symlink_to(outside, target_is_directory=True)
        self.assert_refused(link)
        self.assert_refused(link / "target")
        self.assertTrue(outside_file.exists())

    def test_keep_protects_symlink_location_as_well_as_its_target(self):
        obj = self.file("build/obj.o")
        artifact = self.base / "release.ipa"
        artifact.write_text("keep")
        link = obj.parent / "release.ipa"
        link.symlink_to(artifact)
        self.assert_refused(obj.parent, keep=[link])
        self.assertTrue(link.is_symlink())
        self.assertTrue(artifact.exists())

    def test_internal_links_are_unlinked_without_following(self):
        outside = self.base / "outside"
        outside.mkdir()
        kept = outside / "source.swift"
        kept.write_text("keep")
        obj = self.file("build/obj.o")
        (obj.parent / "framework-link").symlink_to(outside, target_is_directory=True)
        code, report = self.run_cleanup(obj.parent, apply=True)
        self.assertEqual(code, 0, report)
        self.assertTrue(kept.exists())

    def test_git_tracked_modified_or_deleted_files_block_removal(self):
        tracked = self.file("build/important.txt")
        subprocess.run(["git", "-C", str(self.project), "add", "--", "build/important.txt"], check=True)
        tracked.write_text("uncommitted work")
        self.assert_refused(tracked.parent)
        self.assertEqual(tracked.read_text(), "uncommitted work")
        tracked.unlink()
        self.assert_refused(tracked.parent)

    def test_nested_repository_blocks_removal(self):
        obj = self.file("build/nested/source.txt")
        subprocess.run(["git", "init", "-q", str(obj.parent)], check=True)
        self.assert_refused(self.project / "build")
        self.assertTrue(obj.exists())

    def test_batch_rejects_all_before_deleting_any(self):
        obj = self.file("build/obj.o")
        source = self.file("src/keep.swift")
        self.assert_refused(obj.parent, source.parent)
        self.assertTrue(obj.exists())

    def test_overlapping_targets_are_refused(self):
        obj = self.file("build/debug/obj.o")
        self.assert_refused(self.project / "build", obj.parent)
        self.assertTrue(obj.exists())

    def test_signing_material_and_nested_deliverable_folder_are_protected(self):
        for name in ["build/signing/release.jks", "build/outputs/app.ipa"]:
            with self.subTest(name=name):
                obj = self.file(name)
                self.assert_refused(self.project / "build")
                self.assertTrue(obj.exists())
                obj.unlink()
                obj.parent.rmdir()

    def test_index_products_blocks_whole_tree_even_without_keep_flag(self):
        obj = self.file(".codex-build/Index.noindex/Build/Intermediates.noindex/obj.o")
        artifact = self.file(".codex-build/Index.noindex/Build/Products/Foo.framework/Foo")
        root = self.project / ".codex-build/Index.noindex"
        self.assert_refused(root)
        self.assertTrue(obj.exists())
        self.assertEqual(artifact.read_text(), "fixture")

    def test_narrow_intermediates_cleanup_preserves_nested_products(self):
        obj = self.file(".codex-build/Index.noindex/Build/Intermediates.noindex/obj.o")
        artifact = self.file(".codex-build/Index.noindex/Build/Products/Foo.framework/Foo")
        products = artifact.parents[1]
        code, report = self.run_cleanup(obj.parent, apply=True, keep=[products])
        self.assertEqual(code, 0, report)
        self.assertFalse(obj.exists())
        self.assertEqual(artifact.read_text(), "fixture")

    def test_frameworks_symbols_archives_and_packages_are_retained(self):
        for index, relative in enumerate(["Foo.framework/Foo", "Foo.xcframework/Info.plist",
                         "Foo.dSYM/Contents/Resources/DWARF/Foo", "Foo.app/Foo",
                         "Foo.xcarchive/Info.plist", "Foo.xcresult/Info.plist",
                         "release.ipa", "release.apk", "release.aab", "libFoo.a"]):
            with self.subTest(relative=relative):
                target = self.project / "build" / ("case-" + str(index))
                artifact = self.file(str(target.relative_to(self.project)) + "/" + relative)
                self.assert_refused(target)
                self.assertTrue(artifact.exists())

    def test_direct_artifact_subtrees_cannot_bypass_retention(self):
        obj = self.file("build/Foo.framework/Objects/obj.o")
        self.assert_refused(obj.parent)
        self.assertTrue(obj.exists())
        product = self.file("build/Index.noindex/Build/Products/plain/obj.o")
        self.assert_refused(product.parent)
        self.assertTrue(product.exists())

    def test_downloaded_packages_and_diagnostic_evidence_are_retained(self):
        for index, relative in enumerate(["SourcePackages/checkouts/lib/source.swift", "Logs/build.txt",
                         "test-results/result.xml", "screenshots/run.png",
                         "validation.xcactivitylog", "validation.log", "signing/key.pem"]):
            with self.subTest(relative=relative):
                target = self.project / "build" / ("case-" + str(index))
                artifact = self.file(str(target.relative_to(self.project)) + "/" + relative)
                self.assert_refused(target)
                self.assertTrue(artifact.exists())

    def test_protected_names_are_case_insensitive(self):
        product = self.file("build/index/BUILD/pRoDuCtS/plain/obj.o")
        self.assert_refused(product.parent)
        dependency = self.file("build/sourcepackages/checkouts/lib/source.swift")
        self.assert_refused(dependency.parent)
        self.assertTrue(product.exists())
        self.assertTrue(dependency.exists())

    def test_artifact_refusal_prevents_other_batch_deletions(self):
        obj = self.file("build/intermediate/obj.o")
        artifact = self.file(".codex-build/cache/App.framework/App")
        self.assert_refused(obj.parent, self.project / ".codex-build/cache")
        self.assertTrue(obj.exists())
        self.assertTrue(artifact.exists())

    def test_non_git_project_is_supported(self):
        other = self.base / "non-git-project"
        other.mkdir()
        self.project = other
        obj = self.file("build/obj.o")
        code, report = self.run_cleanup(obj.parent, apply=True)
        self.assertEqual(code, 0, report)
        self.assertFalse(obj.exists())

    def test_traversal_and_glob_paths_are_refused(self):
        obj = self.file("build/obj.o")
        for target in [str(self.project) + "/build/../build", str(self.project) + "/build*"]:
            self.assert_refused(target)
        self.assertTrue(obj.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

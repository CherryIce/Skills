"""Focused tests for iOS export-compliance declaration inspection."""

from pathlib import Path
import plistlib
import tempfile
import unittest

import flutter_release_preflight as preflight


class ExportComplianceDeclarationTests(unittest.TestCase):
    def write_plist(self, project: Path, value: bool) -> None:
        path = project / "ios" / "Runner" / "Info.plist"
        path.parent.mkdir(parents=True)
        with path.open("wb") as stream:
            plistlib.dump({"ITSAppUsesNonExemptEncryption": value}, stream)

    def write_project_settings(self, project: Path, generated: str, declaration: str) -> None:
        path = project / "ios" / "Runner.xcodeproj" / "project.pbxproj"
        path.parent.mkdir(parents=True)
        path.write_text(
            "\n".join(
                (
                    f"GENERATE_INFOPLIST_FILE = {generated};",
                    f"INFOPLIST_KEY_ITSAppUsesNonExemptEncryption = {declaration};",
                )
            ),
            encoding="utf-8",
        )

    def test_explicit_false_plist_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.write_plist(project, False)
            facts = preflight.source_export_compliance_facts(project)
            self.assertEqual(facts["source"], "Info.plist")
            self.assertIs(facts["value"], False)
            self.assertTrue(facts["is_false"])

    def test_true_plist_is_not_accepted_as_false(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.write_plist(project, True)
            facts = preflight.source_export_compliance_facts(project)
            self.assertIs(facts["value"], True)
            self.assertFalse(facts["is_false"])

    def test_string_false_plist_is_not_accepted_as_boolean_false(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            path = project / "ios" / "Runner" / "Info.plist"
            path.parent.mkdir(parents=True)
            with path.open("wb") as stream:
                plistlib.dump({"ITSAppUsesNonExemptEncryption": "false"}, stream)
            facts = preflight.source_export_compliance_facts(project)
            self.assertEqual(facts["value"], "false")
            self.assertFalse(facts["is_false"])

    def test_generated_plist_no_build_setting_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.write_project_settings(project, "YES", "NO")
            facts = preflight.source_export_compliance_facts(project)
            self.assertEqual(facts["source"], "Xcode build setting")
            self.assertIs(facts["value"], False)
            self.assertTrue(facts["is_false"])

    def test_build_setting_is_ignored_when_plist_generation_is_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.write_project_settings(project, "NO", "NO")
            facts = preflight.source_export_compliance_facts(project)
            self.assertIsNone(facts["source"])
            self.assertFalse(facts["is_false"])


if __name__ == "__main__":
    unittest.main()

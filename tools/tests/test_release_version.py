# SPDX-License-Identifier: MPL-2.0
import datetime
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "release_version.py"
SPEC = importlib.util.spec_from_file_location("release_version", SCRIPT)
VERSION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERSION)


class ReleaseVersionTests(unittest.TestCase):
    def test_first_release_in_week(self):
        self.assertEqual(VERSION.next_version(datetime.date(2026, 10, 31), []), "2026.44.0")

    def test_sequence_uses_highest_tag_not_tag_count(self):
        tags = ["v2026.44.0", "v2026.44.7", "v2026.43.100", "v2026.44.8-rc1", "v2026.44.09"]
        self.assertEqual(VERSION.next_version(datetime.date(2026, 10, 31), tags), "2026.44.8")

    def test_iso_year_at_new_year(self):
        self.assertEqual(VERSION.next_version(datetime.date(2027, 1, 1), ["v2026.53.2"]), "2026.53.3")

    def test_week_has_no_leading_zero(self):
        self.assertEqual(VERSION.next_version(datetime.date(2027, 1, 4), []), "2027.1.0")

    def test_msi_calendar_version(self):
        self.assertEqual(VERSION.msi_version("2026.44.3"), "26.44.3")
        self.assertEqual(VERSION.msi_version("2026.53.65535"), "26.53.65535")

    def test_explicit_legacy_package_is_reproducible(self):
        self.assertEqual(VERSION.msi_version("0.1.1"), "0.1.1")

    def test_invalid_and_out_of_range_versions_fail(self):
        for version in ["2026.044.0", "2026.0.0", "2026.54.0", "2027.53.0", "2026.44.65536",
                        "2256.1.0", "256.1.0", "1.256.0", "2026.44.0-rc1", "2026.44.0\n"]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                VERSION.msi_version(version)

    def test_exhausted_week_fails(self):
        with self.assertRaises(ValueError):
            VERSION.next_version(datetime.date(2026, 10, 31), ["v2026.44.65535"])

    def test_cli_emits_one_consistent_metadata_set(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "outputs"
            result = subprocess.run([sys.executable, str(SCRIPT), "--version", "2026.44.2", "--json",
                                     "--github-output", str(output)], capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), {"version": "2026.44.2", "tag": "v2026.44.2", "msi": "26.44.2"})
            self.assertEqual(output.read_text(), "version=2026.44.2\ntag=v2026.44.2\nmsi=26.44.2\n")

    def test_missing_git_history_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(SCRIPT), "--root", folder], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()

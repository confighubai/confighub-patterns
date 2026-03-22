#!/usr/bin/env python3
"""Tests for control/framework taxonomy summary builder."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build-control-taxonomy-summary.py"
FIXTURES = REPO_ROOT / "test" / "fixtures" / "validate-content"


class BuildControlTaxonomySummaryTests(unittest.TestCase):
    def run_script(self, fixture_name: str) -> subprocess.CompletedProcess[str]:
        fixture_root = FIXTURES / fixture_name
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "summary.json"
            return subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(fixture_root),
                    "--source-repo",
                    str(fixture_root / "missing-source-repo"),
                    "--out",
                    str(out_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_valid_fixture_builds_summary(self) -> None:
        fixture_root = FIXTURES / "valid"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "summary.json"
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(fixture_root),
                    "--source-repo",
                    str(fixture_root / "missing-source-repo"),
                    "--out",
                    str(out_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            summary = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["control_count"], 1)
            self.assertEqual(summary["framework_count"], 1)
            self.assertEqual(summary["pattern_coverage_count"], 2)
            self.assertEqual(summary["family_counts"], {"gitops-operators": 1})

    def test_missing_control_reference_fails(self) -> None:
        result = self.run_script("invalid_missing_control")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown control_ids", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

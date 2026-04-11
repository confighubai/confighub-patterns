#!/usr/bin/env python3
"""Tests for control/framework bundle builder."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build-control-framework-bundle.py"
FIXTURES = REPO_ROOT / "test" / "fixtures" / "build-control-framework-bundle"


class BuildControlFrameworkBundleTests(unittest.TestCase):
    def test_valid_fixture_builds_bundle(self) -> None:
        fixture_root = FIXTURES / "valid"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "bundle.json"
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(fixture_root),
                    "--summary",
                    str(fixture_root / "summary.json"),
                    "--catalog",
                    str(fixture_root / "catalog.json"),
                    "--out",
                    str(out_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            bundle = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(bundle["control_count"], 1)
            self.assertEqual(bundle["framework_count"], 1)
            self.assertEqual(bundle["pattern_coverage_count"], 2)
            self.assertEqual(bundle["controls"][0]["pattern_refs"][0]["name"], "Application sync failed")
            self.assertEqual(bundle["controls"][0]["example_refs"][0]["repo"], "confighub-scan")
            self.assertEqual(bundle["controls"][0]["example_refs"][0]["path"], "examples/gitops-good-baselines/argocd-application-good.yaml")
            self.assertEqual(bundle["frameworks"][0]["controls"][0]["name"], "Sample GitOps control")

    def test_missing_catalog_pattern_fails(self) -> None:
        fixture_root = FIXTURES / "invalid_missing_pattern"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "bundle.json"
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(fixture_root),
                    "--summary",
                    str(fixture_root / "summary.json"),
                    "--catalog",
                    str(fixture_root / "catalog.json"),
                    "--out",
                    str(out_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing catalog entry", result.stdout + result.stderr)

    def test_check_ignores_machine_local_path_fields(self) -> None:
        fixture_root = FIXTURES / "valid"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "bundle.json"
            build_result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(fixture_root),
                    "--summary",
                    str(fixture_root / "summary.json"),
                    "--catalog",
                    str(fixture_root / "catalog.json"),
                    "--out",
                    str(out_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build_result.returncode, 0, build_result.stderr or build_result.stdout)
            bundle = json.loads(out_path.read_text(encoding="utf-8"))
            bundle["repo_root"] = "/tmp/other-machine/confighub-patterns"
            bundle["source_summary"] = "/tmp/other-machine/summary.json"
            bundle["source_catalog"] = "/tmp/other-machine/catalog.json"
            out_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

            check_result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(fixture_root),
                    "--summary",
                    str(fixture_root / "summary.json"),
                    "--catalog",
                    str(fixture_root / "catalog.json"),
                    "--out",
                    str(out_path),
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(check_result.returncode, 0, check_result.stderr or check_result.stdout)


if __name__ == "__main__":
    unittest.main()

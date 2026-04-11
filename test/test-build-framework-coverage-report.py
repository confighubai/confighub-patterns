#!/usr/bin/env python3
"""Tests for framework coverage report builder."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build-framework-coverage-report.py"


class BuildFrameworkCoverageReportTests(unittest.TestCase):
    def write_json(self, path: Path, doc: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    def test_builds_report_with_cross_family_framework(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle = root / "bundle.json"
            output = root / "report.json"
            self.write_json(
                bundle,
                {
                    "schema_version": "control-framework-bundle-v1",
                    "controls": [
                        {
                            "id": "CTRL-GITOPS-0001",
                            "slug": "gitops-health",
                            "name": "GitOps health",
                            "family": "gitops-operators",
                            "severity": "high",
                            "supported_surfaces": ["live_state", "repo_vs_live"],
                            "supported_consumers": ["cli", "confighub"],
                            "detection_modes": ["native_rule", "derived_comparison"],
                            "pattern_refs": [{"id": "CCVE-2025-0001"}],
                        },
                        {
                            "id": "CTRL-NET-0001",
                            "slug": "network-baseline",
                            "name": "Network baseline",
                            "family": "network-exposure",
                            "severity": "warning",
                            "supported_surfaces": ["static"],
                            "supported_consumers": ["cli", "sdk"],
                            "detection_modes": ["native_rule"],
                            "pattern_refs": [{"id": "CCVE-2025-0002"}],
                        },
                    ],
                    "frameworks": [
                        {
                            "id": "FRM-PLATFORM-0001",
                            "slug": "platform-best",
                            "name": "Platform best",
                            "family": "platform-best",
                            "maturity": "seeded",
                            "platforms": ["kubernetes", "argocd"],
                            "tags": ["platform", "baseline"],
                            "control_ids": ["CTRL-GITOPS-0001", "CTRL-NET-0001"],
                        }
                    ],
                },
            )
            result = subprocess.run(
                ["python3", str(SCRIPT), "--bundle", str(bundle), "--out", str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["framework_count"], 1)
            self.assertEqual(report["cross_family_framework_ids"], ["FRM-PLATFORM-0001"])
            framework = report["frameworks"][0]
            self.assertEqual(framework["pattern_coverage_count"], 2)
            self.assertEqual(framework["control_families"], ["gitops-operators", "network-exposure"])
            self.assertEqual(framework["severity_counts"], {"high": 1, "warning": 1})

    def test_invalid_schema_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle = root / "bundle.json"
            output = root / "report.json"
            self.write_json(bundle, {"schema_version": "wrong"})
            result = subprocess.run(
                ["python3", str(SCRIPT), "--bundle", str(bundle), "--out", str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("schema_version must be", result.stdout + result.stderr)

    def test_check_ignores_machine_local_path_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle = root / "bundle.json"
            output = root / "report.json"
            self.write_json(
                bundle,
                {
                    "schema_version": "control-framework-bundle-v1",
                    "controls": [
                        {
                            "id": "CTRL-GITOPS-0001",
                            "slug": "gitops-health",
                            "name": "GitOps health",
                            "family": "gitops-operators",
                            "severity": "high",
                            "supported_surfaces": ["live_state"],
                            "supported_consumers": ["cli"],
                            "detection_modes": ["native_rule"],
                            "pattern_refs": [{"id": "CCVE-2025-0001"}],
                        }
                    ],
                    "frameworks": [
                        {
                            "id": "FRM-PLATFORM-0001",
                            "slug": "platform-best",
                            "name": "Platform best",
                            "family": "platform-best",
                            "maturity": "seeded",
                            "platforms": ["kubernetes"],
                            "tags": ["platform"],
                            "control_ids": ["CTRL-GITOPS-0001"],
                        }
                    ],
                },
            )
            build_result = subprocess.run(
                ["python3", str(SCRIPT), "--bundle", str(bundle), "--out", str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build_result.returncode, 0, build_result.stderr or build_result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            report["source_bundle"] = "/tmp/other-machine/bundle.json"
            output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

            check_result = subprocess.run(
                ["python3", str(SCRIPT), "--bundle", str(bundle), "--out", str(output), "--check"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(check_result.returncode, 0, check_result.stderr or check_result.stdout)


if __name__ == "__main__":
    unittest.main()

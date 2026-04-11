#!/usr/bin/env python3
"""Tests for control/framework projection validator."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate-control-projections.py"
CONTROL_SCHEMA = REPO_ROOT / "schema" / "control-framework-bundle-v1.schema.json"
REPORT_SCHEMA = REPO_ROOT / "schema" / "framework-coverage-report-v1.schema.json"


class ValidateControlProjectionsTests(unittest.TestCase):
    def write_json(self, path: Path, doc: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    def test_valid_projection_pair_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle = root / "bundle.json"
            report = root / "report.json"
            self.write_json(
                bundle,
                {
                    "schema_version": "control-framework-bundle-v1",
                    "generated_at": "2026-04-11T10:00:00Z",
                    "repo_root": "/tmp/repo",
                    "source_summary": "/tmp/repo/dist/control-taxonomy-summary-v1.json",
                    "source_catalog": "/tmp/repo/dist/risk-catalog-v1.json",
                    "control_count": 1,
                    "framework_count": 1,
                    "pattern_coverage_count": 1,
                    "control_ids": ["CTRL-GITOPS-0001"],
                    "framework_ids": ["FRM-GITOPS-0001"],
                    "pattern_ids": ["CCVE-2025-0001"],
                    "controls": [
                        {
                            "id": "CTRL-GITOPS-0001",
                            "slug": "gitops-health",
                            "name": "GitOps health",
                            "family": "gitops-operators",
                            "summary": "Detect GitOps health failures.",
                            "description": "Detailed description.",
                            "maturity": "seeded",
                            "severity": "high",
                            "supported_surfaces": ["live_state"],
                            "supported_consumers": ["cli", "ai"],
                            "detection_modes": ["native_rule"],
                            "resource_kinds": ["Application"],
                            "tags": ["gitops"],
                            "example_refs": [],
                            "source_path": "/tmp/repo/controls/gitops/gitops-health.yaml",
                            "remediation": {
                                "strategy": "diagnose_then_fix",
                                "safety_class": "review_required",
                                "guidance": ["Look at reconcile errors first."]
                            },
                            "evidence_expectations": {
                                "intent_signals": ["spec.syncPolicy"],
                                "live_signals": ["status.health.status"],
                                "corroborating_sources": ["argocd app get"]
                            },
                            "pattern_refs": [
                                {
                                    "id": "CCVE-2025-0001",
                                    "name": "Git source not ready",
                                    "category": "STATE",
                                    "track": "misconfiguration",
                                    "confidence": "high",
                                    "tags": ["gitops"],
                                    "severity": {
                                        "bucket": "high",
                                        "raw": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    "frameworks": [
                        {
                            "id": "FRM-GITOPS-0001",
                            "slug": "gitops-operators",
                            "name": "GitOps operators",
                            "family": "gitops-operators",
                            "summary": "Operator bundle.",
                            "description": "Framework description.",
                            "maturity": "seeded",
                            "platforms": ["argocd"],
                            "tags": ["gitops"],
                            "outcomes": ["Make GitOps issues easier to triage."],
                            "source_path": "/tmp/repo/frameworks/gitops-operators.yaml",
                            "control_ids": ["CTRL-GITOPS-0001"],
                            "controls": [
                                {
                                    "id": "CTRL-GITOPS-0001",
                                    "slug": "gitops-health",
                                    "name": "GitOps health",
                                    "family": "gitops-operators",
                                    "severity": "high"
                                }
                            ]
                        }
                    ]
                },
            )
            self.write_json(
                report,
                {
                    "schema_version": "framework-coverage-report-v1",
                    "generated_at": "2026-04-11T10:00:00Z",
                    "source_bundle": str(bundle),
                    "framework_count": 1,
                    "cross_family_framework_ids": [],
                    "frameworks": [
                        {
                            "id": "FRM-GITOPS-0001",
                            "slug": "gitops-operators",
                            "name": "GitOps operators",
                            "family": "gitops-operators",
                            "maturity": "seeded",
                            "platforms": ["argocd"],
                            "tags": ["gitops"],
                            "control_ids": ["CTRL-GITOPS-0001"],
                            "control_count": 1,
                            "control_families": ["gitops-operators"],
                            "pattern_ids": ["CCVE-2025-0001"],
                            "pattern_coverage_count": 1,
                            "supported_surfaces": ["live_state"],
                            "supported_consumers": ["ai", "cli"],
                            "detection_modes": ["native_rule"],
                            "severity_counts": {"high": 1}
                        }
                    ]
                },
            )
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--control-bundle-schema",
                    str(CONTROL_SCHEMA),
                    "--framework-report-schema",
                    str(REPORT_SCHEMA),
                    "--control-bundle",
                    str(bundle),
                    "--framework-report",
                    str(report),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("Control/framework projection validation passed", result.stdout)

    def test_semantic_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle = root / "bundle.json"
            report = root / "report.json"
            self.write_json(
                bundle,
                {
                    "schema_version": "control-framework-bundle-v1",
                    "generated_at": "2026-04-11T10:00:00Z",
                    "repo_root": "/tmp/repo",
                    "source_summary": "/tmp/repo/dist/control-taxonomy-summary-v1.json",
                    "source_catalog": "/tmp/repo/dist/risk-catalog-v1.json",
                    "control_count": 2,
                    "framework_count": 0,
                    "pattern_coverage_count": 0,
                    "control_ids": ["CTRL-GITOPS-0001"],
                    "framework_ids": [],
                    "pattern_ids": [],
                    "controls": [],
                    "frameworks": []
                },
            )
            self.write_json(
                report,
                {
                    "schema_version": "framework-coverage-report-v1",
                    "generated_at": "2026-04-11T10:00:00Z",
                    "source_bundle": str(bundle),
                    "framework_count": 0,
                    "cross_family_framework_ids": [],
                    "frameworks": []
                },
            )
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--control-bundle-schema",
                    str(CONTROL_SCHEMA),
                    "--framework-report-schema",
                    str(REPORT_SCHEMA),
                    "--control-bundle",
                    str(bundle),
                    "--framework-report",
                    str(report),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("control_count does not match controls length", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

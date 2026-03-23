#!/usr/bin/env python3
"""Tests for patterns repo bundle manifest builder."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build-bundle-manifest.py"


class BuildBundleManifestTests(unittest.TestCase):
    def write_json(self, path: Path, doc: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    def test_builds_manifest_with_optional_control_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            catalog = root / "dist" / "risk-catalog-v1.json"
            links = root / "dist" / "risk-function-links-v1.json"
            kyverno = root / "mappings" / "kyverno" / "kyverno-ccve-mappings-v1.json"
            trivy = root / "mappings" / "trivy" / "trivy-ccve-mappings-v1.json"
            mapping = root / "dist" / "quality" / "cross-tool-mapping-v1.json"
            control_summary = root / "dist" / "control-taxonomy-summary-v1.json"
            control_bundle = root / "dist" / "control-framework-bundle-v1.json"
            output = root / "dist" / "bundle-manifest-v1.json"

            self.write_json(catalog, {"schema_version": "risk-catalog-v1"})
            self.write_json(links, {"schema_version": "risk-function-links-v1"})
            self.write_json(kyverno, {"schema_version": "kyverno-ccve-mappings-v1", "mappings": []})
            self.write_json(trivy, {"schema_version": "trivy-ccve-mappings-v1", "mappings": []})
            self.write_json(mapping, {"schema_version": "cross-tool-mapping-v1"})
            self.write_json(control_summary, {"schema_version": "control-taxonomy-summary-v1"})
            self.write_json(control_bundle, {"schema_version": "control-framework-bundle-v1"})

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--catalog",
                    str(catalog),
                    "--risk-function-links",
                    str(links),
                    "--kyverno-mappings",
                    str(kyverno),
                    "--trivy-mappings",
                    str(trivy),
                    "--cross-tool-mapping",
                    str(mapping),
                    "--control-taxonomy-summary",
                    str(control_summary),
                    "--control-framework-bundle",
                    str(control_bundle),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            names = [item["name"] for item in manifest["files"]]
            self.assertIn("risk-catalog", names)
            self.assertIn("kyverno-ccve-mappings", names)
            self.assertIn("trivy-ccve-mappings", names)
            self.assertIn("control-taxonomy-summary", names)
            self.assertIn("control-framework-bundle", names)

            check_result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--catalog",
                    str(catalog),
                    "--risk-function-links",
                    str(links),
                    "--kyverno-mappings",
                    str(kyverno),
                    "--trivy-mappings",
                    str(trivy),
                    "--cross-tool-mapping",
                    str(mapping),
                    "--control-taxonomy-summary",
                    str(control_summary),
                    "--control-framework-bundle",
                    str(control_bundle),
                    "--output",
                    str(output),
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(check_result.returncode, 0, check_result.stderr or check_result.stdout)


if __name__ == "__main__":
    unittest.main()

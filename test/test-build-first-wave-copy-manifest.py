#!/usr/bin/env python3
"""Tests for first-wave copy manifest builder."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build-first-wave-copy-manifest.py"


class BuildFirstWaveCopyManifestTests(unittest.TestCase):
    def test_check_ignores_machine_local_path_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_repo = root / "confighub-scan"
            source_repo.mkdir(parents=True, exist_ok=True)
            output = root / "first-wave-copy-manifest-v1.json"

            build_result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--source-repo",
                    str(source_repo),
                    "--out",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build_result.returncode, 0, build_result.stderr or build_result.stdout)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            manifest["source_repo"] = "/tmp/other-machine/confighub-scan"
            manifest["target_repo"] = "/tmp/other-machine/confighub-patterns"
            output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            check_result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--source-repo",
                    str(source_repo),
                    "--out",
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

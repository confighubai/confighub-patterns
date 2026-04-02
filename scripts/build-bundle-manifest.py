#!/usr/bin/env python3
"""Build a release bundle manifest for confighub-patterns artifacts."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

OUTPUT_SCHEMA = "bundle-manifest-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-version", default="dev", help="Bundle version label")
    parser.add_argument("--source-repo", default="confighubai/confighub-patterns", help="Source repository label")
    parser.add_argument("--catalog", default="dist/risk-catalog-v1.json", help="Path to risk catalog")
    parser.add_argument("--risk-function-links", default="dist/risk-function-links-v1.json", help="Path to risk/function links")
    parser.add_argument("--kyverno-mappings", default="mappings/kyverno/kyverno-ccve-mappings-v1.json", help="Path to Kyverno mapping file")
    parser.add_argument("--trivy-mappings", default="mappings/trivy/trivy-ccve-mappings-v1.json", help="Path to Trivy mapping file")
    parser.add_argument("--kubescape-mappings", default="mappings/kubescape/kubescape-ccve-mappings-v1.json", help="Path to Kubescape mapping file")
    parser.add_argument("--cross-tool-mapping", default="dist/quality/cross-tool-mapping-v1.json", help="Path to cross-tool mapping artifact")
    parser.add_argument("--helm-pattern-db", default="dist/helm-pattern-database-v1.json", help="Path to Helm pattern database artifact")
    parser.add_argument("--control-taxonomy-summary", default="dist/control-taxonomy-summary-v1.json", help="Path to control taxonomy summary artifact")
    parser.add_argument("--control-framework-bundle", default="dist/control-framework-bundle-v1.json", help="Path to control/framework bundle artifact")
    parser.add_argument("--framework-coverage-report", default="dist/framework-coverage-report-v1.json", help="Path to framework coverage report artifact")
    parser.add_argument("--external-evidence-schema", default="schema/external-evidence-v1.schema.json", help="Path to external evidence JSON schema")
    parser.add_argument("--output", default="dist/bundle-manifest-v1.json", help="Output path")
    parser.add_argument("--check", action="store_true", help="Check mode: fail if output differs on disk")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level object")
    return data


def json_bytes(doc: Any) -> bytes:
    return (json.dumps(doc, indent=2) + "\n").encode("utf-8")


def normalize_for_check(doc: Any) -> Any:
    if not isinstance(doc, dict):
        return doc
    normalized = dict(doc)
    normalized["published_at"] = "<normalized>"
    return normalized


def check_output(path: Path, doc: dict[str, Any]) -> tuple[bool, str]:
    want = normalize_for_check(doc)
    got = normalize_for_check(load_json(path)) if path.exists() else {}
    if got == want:
        return True, ""
    diff = "".join(
        difflib.unified_diff(
            json_bytes(got).decode("utf-8").splitlines(keepends=True),
            json_bytes(want).decode("utf-8").splitlines(keepends=True),
            fromfile=str(path),
            tofile="generated",
        )
    )
    return False, diff


def write_output(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(doc))


def schema_version(path: Path) -> str:
    try:
        doc = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return ""
    value = doc.get("schema_version")
    return value.strip() if isinstance(value, str) else ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    entries = [
        ("risk-catalog", Path(args.catalog), True),
        ("risk-function-links", Path(args.risk_function_links), True),
        ("kyverno-ccve-mappings", Path(args.kyverno_mappings), True),
        ("trivy-ccve-mappings", Path(args.trivy_mappings), True),
        ("kubescape-ccve-mappings", Path(args.kubescape_mappings), True),
        ("cross-tool-mapping", Path(args.cross_tool_mapping), True),
        ("helm-pattern-database", Path(args.helm_pattern_db), False),
        ("control-taxonomy-summary", Path(args.control_taxonomy_summary), False),
        ("control-framework-bundle", Path(args.control_framework_bundle), False),
        ("framework-coverage-report", Path(args.framework_coverage_report), False),
        ("external-evidence-schema", Path(args.external_evidence_schema), False),
    ]

    files: list[dict[str, Any]] = []
    for name, path, required in entries:
        if not path.exists():
            if required:
                raise FileNotFoundError(path)
            continue
        files.append(
            {
                "name": name,
                "path": str(path),
                "schema_version": schema_version(path),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
                "required": required,
            }
        )

    return {
        "schema_version": OUTPUT_SCHEMA,
        "published_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "bundle_version": args.bundle_version,
        "source_repo": args.source_repo,
        "files": files,
    }


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    doc = build_manifest(args)

    if args.check:
        ok, diff = check_output(output_path, doc)
        if not ok:
            print(diff)
            return 1
        print(f"bundle manifest up to date: {output_path}")
        return 0

    write_output(output_path, doc)
    print(f"Wrote bundle manifest to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

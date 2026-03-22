#!/usr/bin/env python3
"""Build a dry-run manifest for the first wave of asset copies from confighub-scan."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SOURCE_REPO = REPO_ROOT.parent / "confighub-scan"
DEFAULT_OUTPUT = REPO_ROOT / "dist" / "first-wave-copy-manifest-v1.json"


@dataclass(frozen=True)
class MoveItem:
    category: str
    source_type: str
    source: str
    destination: str


MOVE_ITEMS: list[MoveItem] = [
    MoveItem("pattern_source", "glob", "risks/*.yaml", "patterns/"),
    MoveItem("pattern_source", "dir", "risks/archive", "patterns/archive"),
    MoveItem("pattern_source", "file", "risks/README.md", "docs/source-risks-README.md"),
    MoveItem("external_mappings", "file", "risks/kyverno/kyverno-ccve-mappings-v1.json", "mappings/kyverno/kyverno-ccve-mappings-v1.json"),
    MoveItem("external_mappings", "file", "risks/trivy/trivy-ccve-mappings-v1.json", "mappings/trivy/trivy-ccve-mappings-v1.json"),
    MoveItem("external_mappings", "file", "scripts/build-cross-tool-mapping.py", "scripts/build-cross-tool-mapping.py"),
    MoveItem("external_mappings", "file", "risks/quality/cross-tool-mapping-policy-v1.json", "quality/cross-tool-mapping-policy-v1.json"),
    MoveItem("schema", "file", "risks/schema/ccve-taxonomy-v1.yaml", "schema/ccve-taxonomy-v1.yaml"),
    MoveItem("schema", "file", "risks/schema/risk-catalog-v1.schema.json", "schema/risk-catalog-v1.schema.json"),
    MoveItem("schema", "file", "risks/schema/helm-pattern-database-v1.schema.json", "schema/helm-pattern-database-v1.schema.json"),
    MoveItem("pattern_quality", "file", "risks/quality/launch-rules-v1.json", "quality/launch-rules-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/promotion-quality-policy-v1.json", "quality/promotion-quality-policy-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/risk-function-link-thresholds-v1.json", "quality/risk-function-link-thresholds-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/severity-calibration-policy-v1.json", "quality/severity-calibration-policy-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/severity-calibration-policy-v2.json", "quality/severity-calibration-policy-v2.json"),
    MoveItem("pattern_quality", "file", "risks/quality/severity-calibration-baseline-v1.json", "quality/severity-calibration-baseline-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/severity-review-sample-policy-v1.json", "quality/severity-review-sample-policy-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/severity-release-decision-policy-v1.json", "quality/severity-release-decision-policy-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/unresolved-external-findings-input-v1.json", "quality/unresolved-external-findings-input-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/unresolved-external-findings-policy-v1.json", "quality/unresolved-external-findings-policy-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/mining-candidate-policy-v1.json", "quality/mining-candidate-policy-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/mining-query-templates-v1.json", "quality/mining-query-templates-v1.json"),
    MoveItem("pattern_quality", "file", "risks/quality/pattern-inventory-overrides-v1.json", "quality/pattern-inventory-overrides-v1.json"),
    MoveItem("pattern_builders", "file", "scripts/classify-remedies.py", "scripts/classify-remedies.py"),
    MoveItem("pattern_builders", "file", "scripts/build-risk-function-links.py", "scripts/build-risk-function-links.py"),
    MoveItem("pattern_builders", "file", "scripts/build-severity-review-sample.py", "scripts/build-severity-review-sample.py"),
    MoveItem("pattern_builders", "file", "scripts/validate-risk-function-links.py", "scripts/validate-risk-function-links.py"),
    MoveItem("pattern_builders", "file", "scripts/validate-severity-calibration.py", "scripts/validate-severity-calibration.py"),
    MoveItem("pattern_builders", "file", "scripts/validate-severity-release-decision.py", "scripts/validate-severity-release-decision.py"),
    MoveItem("released_bundles", "file", "dist/risk-catalog-v1.json", "dist/risk-catalog-v1.json"),
    MoveItem("released_bundles", "file", "dist/risk-function-links-v1.json", "dist/risk-function-links-v1.json"),
    MoveItem("released_bundles", "file", "dist/helm-pattern-database-v1.json", "dist/helm-pattern-database-v1.json"),
    MoveItem("released_bundles", "file", "dist/quality/cross-tool-mapping-v1.json", "dist/quality/cross-tool-mapping-v1.json"),
    MoveItem("released_bundles", "file", "dist/quality/pattern-inventory-v1.json", "dist/quality/pattern-inventory-v1.json"),
    MoveItem("released_bundles", "file", "dist/quality/pattern-inventory-summary-v1.json", "dist/quality/pattern-inventory-summary-v1.json"),
    MoveItem("released_bundles", "file", "dist/quality/pattern-queue-report-v1.json", "dist/quality/pattern-queue-report-v1.json"),
    MoveItem("released_bundles", "file", "dist/quality/mining-candidate-queue-v1.json", "dist/quality/mining-candidate-queue-v1.json"),
    MoveItem("released_bundles", "file", "dist/quality/severity-review-sample-v1.json", "dist/quality/severity-review-sample-v1.json"),
    MoveItem("released_bundles", "file", "dist/quality/unresolved-external-findings-rollout-v1.json", "dist/quality/unresolved-external-findings-rollout-v1.json"),
]


def summarize_source(source_repo: Path, item: MoveItem) -> dict[str, Any]:
    source_path = source_repo / item.source
    entry: dict[str, Any] = {
        "category": item.category,
        "source_type": item.source_type,
        "source": item.source,
        "destination": item.destination,
        "target": item.destination,
    }

    if item.source_type == "glob":
        matches = sorted(source_repo.glob(item.source))
        entry["exists"] = bool(matches)
        entry["match_count"] = len(matches)
        entry["samples"] = [str(path.relative_to(source_repo)) for path in matches[:5]]
        return entry

    entry["exists"] = source_path.exists()
    if source_path.is_file():
        entry["size_bytes"] = source_path.stat().st_size
    elif source_path.is_dir():
        files = [path for path in source_path.rglob("*") if path.is_file()]
        entry["file_count"] = len(files)
        entry["samples"] = [str(path.relative_to(source_repo)) for path in files[:5]]
    return entry


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_target_state(source_repo: Path, entry: dict[str, Any]) -> dict[str, Any]:
    source_path = source_repo / entry["source"]
    target_path = REPO_ROOT / entry["destination"]
    entry["target_exists"] = target_path.exists()

    if not entry["exists"]:
        entry["copy_status"] = "missing_source"
        return entry

    if entry["source_type"] == "file":
        if source_path.is_file():
            entry["source_sha256"] = file_sha256(source_path)
        if target_path.is_file():
            entry["target_sha256"] = file_sha256(target_path)
        if not target_path.exists():
            entry["copy_status"] = "ready_not_copied"
        elif entry.get("source_sha256") == entry.get("target_sha256"):
            entry["copy_status"] = "copied_matching"
        else:
            entry["copy_status"] = "copied_drifted"
        return entry

    if entry["source_type"] == "dir":
        source_files = [path for path in source_path.rglob("*") if path.is_file()]
        target_files = [path for path in target_path.rglob("*") if path.is_file()] if target_path.exists() else []
        entry["target_file_count"] = len(target_files)
        if not target_path.exists():
            entry["copy_status"] = "ready_not_copied"
        elif len(source_files) == len(target_files):
            entry["copy_status"] = "copied_matching"
        else:
            entry["copy_status"] = "copy_incomplete"
        return entry

    source_glob = entry["source"]
    target_glob = str(Path(entry["destination"]) / Path(source_glob).name)
    target_matches = sorted(REPO_ROOT.glob(target_glob))
    entry["target_match_count"] = len(target_matches)
    entry["target_samples"] = [str(path.relative_to(REPO_ROOT)) for path in target_matches[:5]]
    if not target_matches:
        entry["copy_status"] = "ready_not_copied"
    elif entry.get("match_count") == len(target_matches):
        entry["copy_status"] = "copied_matching"
    else:
        entry["copy_status"] = "copy_incomplete"
    return entry


def build_manifest(source_repo: Path) -> dict[str, Any]:
    items = [add_target_state(source_repo, summarize_source(source_repo, item)) for item in MOVE_ITEMS]
    missing = [item["source"] for item in items if not item["exists"]]
    copy_status_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for item in items:
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1
        copy_status = item["copy_status"]
        copy_status_counts[copy_status] = copy_status_counts.get(copy_status, 0) + 1

    return {
        "schema_version": "first-wave-copy-manifest-v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_repo": str(source_repo.resolve()),
        "target_repo": str(REPO_ROOT.resolve()),
        "item_count": len(items),
        "missing_count": len(missing),
        "missing_sources": missing,
        "category_counts": category_counts,
        "copy_status_counts": copy_status_counts,
        "items": items,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_manifest(path: Path, manifest: dict[str, Any]) -> int:
    if not path.exists():
        print(f"missing manifest: {path}")
        return 1

    current = json.loads(path.read_text(encoding="utf-8"))
    expected = dict(manifest)
    current.pop("generated_at", None)
    expected.pop("generated_at", None)
    if current != expected:
        print(f"manifest out of date: {path}")
        return 1

    print(f"manifest up to date: {path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, default=DEFAULT_SOURCE_REPO)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args.source_repo.resolve())
    if args.check:
        return check_manifest(args.out, manifest)

    write_manifest(args.out, manifest)
    print(
        f"wrote {args.out} "
        f"({manifest['item_count']} items, {manifest['missing_count']} missing, "
        f"copy states: {manifest['copy_status_counts']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

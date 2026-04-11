#!/usr/bin/env python3
"""Build a bundle artifact for promoted controls and frameworks."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SUMMARY = REPO_ROOT / "dist" / "control-taxonomy-summary-v1.json"
DEFAULT_CATALOG = REPO_ROOT / "dist" / "risk-catalog-v1.json"
DEFAULT_OUTPUT = REPO_ROOT / "dist" / "control-framework-bundle-v1.json"

SUMMARY_SCHEMA = "control-taxonomy-summary-v1"
CATALOG_SCHEMA = "risk-catalog-v1"
OUTPUT_SCHEMA = "control-framework-bundle-v1"


class BundleError(RuntimeError):
    """Raised when the source content cannot be assembled into a bundle."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise BundleError(f"{path}: expected top-level object")
    return doc


def load_yaml(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise BundleError(f"{path}: expected top-level mapping")
    return doc


def build_pattern_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if catalog.get("schema_version") != CATALOG_SCHEMA:
        raise BundleError(f"catalog schema_version must be {CATALOG_SCHEMA!r}")
    entries = catalog.get("entries")
    if not isinstance(entries, list):
        raise BundleError("catalog entries must be a list")

    index: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        pattern_id = entry.get("id")
        if not isinstance(pattern_id, str) or not pattern_id:
            continue
        index[pattern_id] = {
            "id": pattern_id,
            "name": entry.get("name"),
            "category": entry.get("category"),
            "track": entry.get("track"),
            "severity": entry.get("severity"),
            "confidence": entry.get("confidence"),
            "tags": entry.get("tags", []),
        }
    return index


def normalize_control_doc(path: Path, summary_row: dict[str, Any], pattern_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    doc = load_yaml(path)
    pattern_ids = summary_row.get("pattern_ids", [])
    if not isinstance(pattern_ids, list):
        raise BundleError(f"{path}: summary pattern_ids must be a list")

    pattern_refs: list[dict[str, Any]] = []
    for pattern_id in pattern_ids:
        if pattern_id not in pattern_index:
            raise BundleError(f"{path}: missing catalog entry for {pattern_id}")
        pattern_refs.append(pattern_index[pattern_id])

    remediation = doc.get("remediation", {})
    evidence = doc.get("evidence_expectations", {})

    return {
        "id": doc.get("id"),
        "slug": doc.get("slug"),
        "name": doc.get("name"),
        "family": doc.get("family"),
        "summary": doc.get("summary"),
        "description": doc.get("description"),
        "maturity": doc.get("maturity"),
        "severity": doc.get("severity"),
        "supported_surfaces": doc.get("supported_surfaces", []),
        "supported_consumers": doc.get("supported_consumers", []),
        "detection_modes": doc.get("detection_modes", []),
        "resource_kinds": doc.get("resource_kinds", []),
        "tags": doc.get("tags", []),
        "example_refs": doc.get("example_refs", []),
        "source_path": str(path),
        "remediation": {
            "strategy": remediation.get("strategy"),
            "safety_class": remediation.get("safety_class"),
            "guidance": remediation.get("guidance", []),
        },
        "evidence_expectations": {
            "intent_signals": evidence.get("intent_signals", []),
            "live_signals": evidence.get("live_signals", []),
            "corroborating_sources": evidence.get("corroborating_sources", []),
        },
        "pattern_refs": pattern_refs,
    }


def normalize_framework_doc(path: Path, control_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    doc = load_yaml(path)
    control_ids = doc.get("control_ids", [])
    if not isinstance(control_ids, list):
        raise BundleError(f"{path}: control_ids must be a list")
    missing = [control_id for control_id in control_ids if control_id not in control_index]
    if missing:
        raise BundleError(f"{path}: unknown control_ids {missing}")

    return {
        "id": doc.get("id"),
        "slug": doc.get("slug"),
        "name": doc.get("name"),
        "family": doc.get("family"),
        "summary": doc.get("summary"),
        "description": doc.get("description"),
        "maturity": doc.get("maturity"),
        "platforms": doc.get("platforms", []),
        "tags": doc.get("tags", []),
        "outcomes": doc.get("outcomes", []),
        "source_path": str(path),
        "control_ids": control_ids,
        "controls": [
            {
                "id": control_index[control_id]["id"],
                "slug": control_index[control_id]["slug"],
                "name": control_index[control_id]["name"],
                "family": control_index[control_id]["family"],
                "severity": control_index[control_id]["severity"],
            }
            for control_id in control_ids
        ],
    }


def build_bundle(repo_root: Path, summary_path: Path, catalog_path: Path) -> dict[str, Any]:
    summary = load_json(summary_path)
    if summary.get("schema_version") != SUMMARY_SCHEMA:
        raise BundleError(f"summary schema_version must be {SUMMARY_SCHEMA!r}")
    catalog = load_json(catalog_path)
    pattern_index = build_pattern_index(catalog)

    summary_controls = summary.get("controls")
    summary_frameworks = summary.get("frameworks")
    if not isinstance(summary_controls, list) or not isinstance(summary_frameworks, list):
        raise BundleError("summary must contain controls and frameworks lists")

    controls: list[dict[str, Any]] = []
    for row in summary_controls:
        if not isinstance(row, dict):
            continue
        path_text = row.get("path")
        if not isinstance(path_text, str) or not path_text:
            raise BundleError("summary control row missing path")
        controls.append(normalize_control_doc(repo_root / path_text, row, pattern_index))
    controls.sort(key=lambda item: item["id"])
    control_index = {item["id"]: item for item in controls}

    frameworks: list[dict[str, Any]] = []
    for row in summary_frameworks:
        if not isinstance(row, dict):
            continue
        path_text = row.get("path")
        if not isinstance(path_text, str) or not path_text:
            raise BundleError("summary framework row missing path")
        frameworks.append(normalize_framework_doc(repo_root / path_text, control_index))
    frameworks.sort(key=lambda item: item["id"])

    unique_pattern_ids = sorted({ref["id"] for control in controls for ref in control["pattern_refs"]})

    return {
        "schema_version": OUTPUT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo_root": str(repo_root.resolve()),
        "source_summary": str(summary_path.resolve()),
        "source_catalog": str(catalog_path.resolve()),
        "control_count": len(controls),
        "framework_count": len(frameworks),
        "pattern_coverage_count": len(unique_pattern_ids),
        "control_ids": [item["id"] for item in controls],
        "framework_ids": [item["id"] for item in frameworks],
        "pattern_ids": unique_pattern_ids,
        "controls": controls,
        "frameworks": frameworks,
    }


def normalize_for_check(doc: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(doc)
    normalized["generated_at"] = "<normalized>"
    normalized["repo_root"] = "<normalized>"
    normalized["source_summary"] = "<normalized>"
    normalized["source_catalog"] = "<normalized>"
    normalized["controls"] = [
        {**item, "source_path": "<normalized>"} if isinstance(item, dict) else item
        for item in normalized.get("controls", [])
    ]
    normalized["frameworks"] = [
        {**item, "source_path": "<normalized>"} if isinstance(item, dict) else item
        for item in normalized.get("frameworks", [])
    ]
    return normalized


def write_bundle(path: Path, bundle: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_bundle(path: Path, bundle: dict[str, Any]) -> int:
    if not path.exists():
        print(f"missing bundle: {path}")
        return 1
    current = load_json(path)
    if normalize_for_check(current) != normalize_for_check(bundle):
        print(f"bundle out of date: {path}")
        return 1
    print(f"bundle up to date: {path}")
    return 0


def main() -> int:
    args = parse_args()
    try:
        bundle = build_bundle(args.repo_root.resolve(), args.summary.resolve(), args.catalog.resolve())
    except BundleError as exc:
        print(exc)
        return 1

    if args.check:
        return check_bundle(args.out, bundle)

    write_bundle(args.out, bundle)
    print(
        f"wrote {args.out} "
        f"({bundle['control_count']} controls, {bundle['framework_count']} frameworks, "
        f"{bundle['pattern_coverage_count']} patterns)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

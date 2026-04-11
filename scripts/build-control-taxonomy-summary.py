#!/usr/bin/env python3
"""Validate control/framework definitions and build a compact summary artifact."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_OUTPUT = REPO_ROOT / "dist" / "control-taxonomy-summary-v1.json"
DEFAULT_SOURCE_REPO = REPO_ROOT.parent / "confighub-scan"

CONTROL_SCHEMA_VERSION = "control-definition-v1"
FRAMEWORK_SCHEMA_VERSION = "framework-definition-v1"
OUTPUT_SCHEMA_VERSION = "control-taxonomy-summary-v1"

CONTROL_FAMILIES = {
    "gitops-operators",
    "workload-hardening",
    "rbac-and-identity",
    "network-exposure",
    "secrets-and-credentials",
    "cluster-hardening",
    "platform-best",
}
MATURITY_VALUES = {"seeded", "candidate", "promoted"}
SEVERITY_VALUES = {"info", "warning", "high", "critical"}
SURFACE_VALUES = {"static", "live_state", "imported_evidence", "connected_validation", "repo_vs_live"}
CONSUMER_VALUES = {"cli", "cub_scout", "confighub", "sdk", "ai"}
DETECTION_MODE_VALUES = {"native_rule", "external_mapping", "sdk_worker", "derived_comparison"}
REMEDIATION_STRATEGIES = {"config_fix", "diagnose_then_fix", "operational_fix", "manual_review"}
SAFETY_CLASSES = {"safe_auto", "review_required", "manual_only", "diagnose_only"}


class ValidationError(RuntimeError):
    """Raised when the taxonomy content is structurally invalid."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--source-repo", type=Path, default=DEFAULT_SOURCE_REPO)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValidationError(f"{path}: expected top-level mapping")
    return doc


def norm_text(value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"expected string, got {type(value).__name__}")
    text = value.strip()
    if not text:
        raise ValidationError("expected non-empty string")
    return text


def norm_string_list(value: Any, *, field: str, allowed: set[str] | None = None) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValidationError(f"{field}: expected non-empty list")
    normalized: list[str] = []
    for raw in value:
        text = norm_text(raw)
        if allowed and text not in allowed:
            raise ValidationError(f"{field}: unsupported value {text!r}")
        normalized.append(text)
    if len(set(normalized)) != len(normalized):
        raise ValidationError(f"{field}: duplicate values are not allowed")
    return normalized


def discover_pattern_ids(source_repo: Path) -> set[str]:
    risks_dir = source_repo / "risks"
    if not risks_dir.exists():
        return set()
    return {path.stem for path in risks_dir.glob("CCVE-*.yaml")}


def validate_control(path: Path, known_patterns: set[str]) -> dict[str, Any]:
    doc = load_yaml(path)
    if doc.get("schema_version") != CONTROL_SCHEMA_VERSION:
        raise ValidationError(f"{path}: schema_version must be {CONTROL_SCHEMA_VERSION!r}")

    control_id = norm_text(doc.get("id"))
    slug = norm_text(doc.get("slug"))
    norm_text(doc.get("name"))
    family = norm_text(doc.get("family"))
    norm_text(doc.get("summary"))
    norm_text(doc.get("description"))
    maturity = norm_text(doc.get("maturity"))
    severity = norm_text(doc.get("severity"))
    if family not in CONTROL_FAMILIES:
        raise ValidationError(f"{path}: unsupported family {family!r}")
    if maturity not in MATURITY_VALUES:
        raise ValidationError(f"{path}: unsupported maturity {maturity!r}")
    if severity not in SEVERITY_VALUES:
        raise ValidationError(f"{path}: unsupported severity {severity!r}")

    supported_surfaces = norm_string_list(doc.get("supported_surfaces"), field=f"{path}: supported_surfaces", allowed=SURFACE_VALUES)
    supported_consumers = norm_string_list(doc.get("supported_consumers"), field=f"{path}: supported_consumers", allowed=CONSUMER_VALUES)
    detection_modes = norm_string_list(doc.get("detection_modes"), field=f"{path}: detection_modes", allowed=DETECTION_MODE_VALUES)
    resource_kinds = norm_string_list(doc.get("resource_kinds"), field=f"{path}: resource_kinds")
    pattern_ids = norm_string_list(doc.get("pattern_ids"), field=f"{path}: pattern_ids")
    tags = norm_string_list(doc.get("tags"), field=f"{path}: tags")

    remediation = doc.get("remediation")
    if not isinstance(remediation, dict):
        raise ValidationError(f"{path}: remediation must be an object")
    strategy = norm_text(remediation.get("strategy"))
    safety_class = norm_text(remediation.get("safety_class"))
    guidance = norm_string_list(remediation.get("guidance"), field=f"{path}: remediation.guidance")
    if strategy not in REMEDIATION_STRATEGIES:
        raise ValidationError(f"{path}: unsupported remediation.strategy {strategy!r}")
    if safety_class not in SAFETY_CLASSES:
        raise ValidationError(f"{path}: unsupported remediation.safety_class {safety_class!r}")

    evidence = doc.get("evidence_expectations")
    if not isinstance(evidence, dict):
        raise ValidationError(f"{path}: evidence_expectations must be an object")
    # Allow empty evidence lists, but preserve validation for non-string values.
    for key in ("intent_signals", "live_signals", "corroborating_sources"):
        raw_list = evidence.get(key, [])
        if raw_list in (None, []):
            evidence[key] = []
            continue
        evidence[key] = norm_string_list(raw_list, field=f"{path}: evidence_expectations.{key}")

    if known_patterns:
        missing = sorted(pattern_id for pattern_id in pattern_ids if pattern_id not in known_patterns)
        if missing:
            raise ValidationError(f"{path}: unknown pattern_ids {missing}")

    return {
        "id": control_id,
        "slug": slug,
        "path": str(path.relative_to(REPO_ROOT)),
        "family": family,
        "maturity": maturity,
        "severity": severity,
        "supported_surfaces": supported_surfaces,
        "supported_consumers": supported_consumers,
        "detection_modes": detection_modes,
        "resource_kinds": resource_kinds,
        "pattern_ids": pattern_ids,
        "tags": tags,
        "remediation_strategy": strategy,
        "remediation_safety_class": safety_class,
        "remediation_guidance_count": len(guidance),
    }


def validate_framework(path: Path, known_controls: set[str]) -> dict[str, Any]:
    doc = load_yaml(path)
    if doc.get("schema_version") != FRAMEWORK_SCHEMA_VERSION:
        raise ValidationError(f"{path}: schema_version must be {FRAMEWORK_SCHEMA_VERSION!r}")

    framework_id = norm_text(doc.get("id"))
    slug = norm_text(doc.get("slug"))
    norm_text(doc.get("name"))
    family = norm_text(doc.get("family"))
    norm_text(doc.get("summary"))
    norm_text(doc.get("description"))
    maturity = norm_text(doc.get("maturity"))
    if family not in CONTROL_FAMILIES:
        raise ValidationError(f"{path}: unsupported family {family!r}")
    if maturity not in MATURITY_VALUES:
        raise ValidationError(f"{path}: unsupported maturity {maturity!r}")

    control_ids = norm_string_list(doc.get("control_ids"), field=f"{path}: control_ids")
    platforms = norm_string_list(doc.get("platforms"), field=f"{path}: platforms")
    tags = norm_string_list(doc.get("tags"), field=f"{path}: tags")
    outcomes = norm_string_list(doc.get("outcomes"), field=f"{path}: outcomes")

    missing = sorted(control_id for control_id in control_ids if control_id not in known_controls)
    if missing:
        raise ValidationError(f"{path}: unknown control_ids {missing}")

    return {
        "id": framework_id,
        "slug": slug,
        "path": str(path.relative_to(REPO_ROOT)),
        "family": family,
        "maturity": maturity,
        "control_ids": control_ids,
        "platforms": platforms,
        "tags": tags,
        "outcomes": outcomes,
    }


def discover_definition_files(root: Path, dirname: str) -> list[Path]:
    base = root / dirname
    if not base.exists():
        return []
    return sorted(path for path in base.rglob("*.yaml") if path.is_file())


def build_summary(repo_root: Path, source_repo: Path) -> dict[str, Any]:
    known_patterns = discover_pattern_ids(source_repo.resolve()) if source_repo.exists() else set()
    controls = [validate_control(path, known_patterns) for path in discover_definition_files(repo_root, "controls")]
    controls.sort(key=lambda item: item["id"])

    control_ids = [item["id"] for item in controls]
    if len(set(control_ids)) != len(control_ids):
        duplicates = [control_id for control_id, count in Counter(control_ids).items() if count > 1]
        raise ValidationError(f"duplicate control ids: {sorted(duplicates)}")

    frameworks = [validate_framework(path, set(control_ids)) for path in discover_definition_files(repo_root, "frameworks")]
    frameworks.sort(key=lambda item: item["id"])
    framework_ids = [item["id"] for item in frameworks]
    if len(set(framework_ids)) != len(framework_ids):
        duplicates = [framework_id for framework_id, count in Counter(framework_ids).items() if count > 1]
        raise ValidationError(f"duplicate framework ids: {sorted(duplicates)}")

    family_counts = Counter(item["family"] for item in controls)
    surface_counts = Counter(surface for item in controls for surface in item["supported_surfaces"])
    consumer_counts = Counter(consumer for item in controls for consumer in item["supported_consumers"])
    detection_mode_counts = Counter(mode for item in controls for mode in item["detection_modes"])
    unique_patterns = sorted({pattern_id for item in controls for pattern_id in item["pattern_ids"]})

    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo_root": str(repo_root.resolve()),
        "source_pattern_repo": str(source_repo.resolve()) if source_repo.exists() else None,
        "pattern_validation_mode": "sibling_confighub_scan" if known_patterns else "skipped",
        "control_count": len(controls),
        "framework_count": len(frameworks),
        "pattern_coverage_count": len(unique_patterns),
        "family_counts": dict(sorted(family_counts.items())),
        "surface_counts": dict(sorted(surface_counts.items())),
        "consumer_counts": dict(sorted(consumer_counts.items())),
        "detection_mode_counts": dict(sorted(detection_mode_counts.items())),
        "control_ids": control_ids,
        "framework_ids": framework_ids,
        "pattern_ids": unique_patterns,
        "controls": controls,
        "frameworks": frameworks,
    }


def normalize_for_check(doc: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(doc)
    normalized["generated_at"] = "<normalized>"
    normalized["pattern_validation_mode"] = "<normalized>"
    normalized["repo_root"] = "<normalized>"
    normalized["source_pattern_repo"] = "<normalized>"
    return normalized


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_summary(path: Path, summary: dict[str, Any]) -> int:
    if not path.exists():
        print(f"missing summary: {path}")
        return 1
    current = json.loads(path.read_text(encoding="utf-8"))
    if normalize_for_check(current) != normalize_for_check(summary):
        print(f"summary out of date: {path}")
        return 1
    print(f"summary up to date: {path}")
    return 0


def main() -> int:
    args = parse_args()
    try:
        summary = build_summary(args.repo_root.resolve(), args.source_repo.resolve())
    except ValidationError as exc:
        print(exc)
        return 1

    if args.check:
        return check_summary(args.out, summary)

    write_summary(args.out, summary)
    print(
        f"wrote {args.out} "
        f"({summary['control_count']} controls, {summary['framework_count']} frameworks, "
        f"{summary['pattern_coverage_count']} patterns)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

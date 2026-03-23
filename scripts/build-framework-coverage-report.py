#!/usr/bin/env python3
"""Build a compact framework coverage report from the promoted taxonomy bundle."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_BUNDLE = REPO_ROOT / "dist" / "control-framework-bundle-v1.json"
DEFAULT_OUTPUT = REPO_ROOT / "dist" / "framework-coverage-report-v1.json"

BUNDLE_SCHEMA = "control-framework-bundle-v1"
OUTPUT_SCHEMA = "framework-coverage-report-v1"


class ReportError(RuntimeError):
    """Raised when the source bundle cannot be converted into a report."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ReportError(f"{path}: expected top-level object")
    return doc


def normalize_for_check(doc: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(doc)
    normalized["generated_at"] = "<normalized>"
    return normalized


def build_report(bundle: dict[str, Any], bundle_path: Path) -> dict[str, Any]:
    if bundle.get("schema_version") != BUNDLE_SCHEMA:
        raise ReportError(f"{bundle_path}: schema_version must be {BUNDLE_SCHEMA!r}")

    controls = bundle.get("controls")
    frameworks = bundle.get("frameworks")
    if not isinstance(controls, list) or not isinstance(frameworks, list):
        raise ReportError(f"{bundle_path}: controls and frameworks must be lists")

    control_index: dict[str, dict[str, Any]] = {}
    for control in controls:
        if not isinstance(control, dict):
            continue
        control_id = control.get("id")
        if isinstance(control_id, str) and control_id:
            control_index[control_id] = control

    framework_rows: list[dict[str, Any]] = []
    cross_family_framework_ids: list[str] = []
    for framework in frameworks:
        if not isinstance(framework, dict):
            continue
        control_ids = framework.get("control_ids", [])
        if not isinstance(control_ids, list):
            raise ReportError("framework control_ids must be a list")
        rows = [control_index[control_id] for control_id in control_ids if control_id in control_index]
        if len(rows) != len(control_ids):
            missing = sorted(set(control_ids) - set(control_index))
            raise ReportError(f"framework {framework.get('id')}: missing controls {missing}")

        pattern_ids = sorted(
            {
                pattern_ref["id"]
                for control in rows
                for pattern_ref in control.get("pattern_refs", [])
                if isinstance(pattern_ref, dict) and isinstance(pattern_ref.get("id"), str)
            }
        )
        control_families = sorted(
            {
                family
                for control in rows
                for family in [control.get("family")]
                if isinstance(family, str) and family
            }
        )
        supported_surfaces = sorted(
            {
                surface
                for control in rows
                for surface in control.get("supported_surfaces", [])
                if isinstance(surface, str) and surface
            }
        )
        supported_consumers = sorted(
            {
                consumer
                for control in rows
                for consumer in control.get("supported_consumers", [])
                if isinstance(consumer, str) and consumer
            }
        )
        detection_modes = sorted(
            {
                mode
                for control in rows
                for mode in control.get("detection_modes", [])
                if isinstance(mode, str) and mode
            }
        )
        severity_counts = Counter(
            control["severity"]
            for control in rows
            if isinstance(control.get("severity"), str) and control["severity"]
        )
        if len(control_families) > 1:
            framework_id = framework.get("id")
            if isinstance(framework_id, str) and framework_id:
                cross_family_framework_ids.append(framework_id)

        framework_rows.append(
            {
                "id": framework.get("id"),
                "slug": framework.get("slug"),
                "name": framework.get("name"),
                "family": framework.get("family"),
                "maturity": framework.get("maturity"),
                "platforms": framework.get("platforms", []),
                "tags": framework.get("tags", []),
                "control_ids": control_ids,
                "control_count": len(control_ids),
                "control_families": control_families,
                "pattern_ids": pattern_ids,
                "pattern_coverage_count": len(pattern_ids),
                "supported_surfaces": supported_surfaces,
                "supported_consumers": supported_consumers,
                "detection_modes": detection_modes,
                "severity_counts": dict(sorted(severity_counts.items())),
            }
        )

    framework_rows.sort(key=lambda item: item["id"] or "")
    return {
        "schema_version": OUTPUT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_bundle": str(bundle_path.resolve()),
        "framework_count": len(framework_rows),
        "cross_family_framework_ids": sorted(cross_family_framework_ids),
        "frameworks": framework_rows,
    }


def write_output(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_output(path: Path, report: dict[str, Any]) -> int:
    if not path.exists():
        print(f"missing report: {path}")
        return 1
    current = load_json(path)
    if normalize_for_check(current) != normalize_for_check(report):
        print(f"report out of date: {path}")
        return 1
    print(f"report up to date: {path}")
    return 0


def main() -> int:
    args = parse_args()
    try:
        report = build_report(load_json(args.bundle), args.bundle)
    except ReportError as exc:
        print(exc)
        return 1

    if args.check:
        return check_output(args.out, report)

    write_output(args.out, report)
    print(
        f"wrote {args.out} "
        f"({report['framework_count']} frameworks, {len(report['cross_family_framework_ids'])} cross-family)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

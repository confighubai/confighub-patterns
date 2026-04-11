#!/usr/bin/env python3
"""Validate control/framework projection schemas and generated artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema package required. Install with: pip install jsonschema")
    sys.exit(1)


CONTROL_BUNDLE_SCHEMA_PATH = Path("schema/control-framework-bundle-v1.schema.json")
FRAMEWORK_REPORT_SCHEMA_PATH = Path("schema/framework-coverage-report-v1.schema.json")
CONTROL_BUNDLE_PATH = Path("dist/control-framework-bundle-v1.json")
FRAMEWORK_REPORT_PATH = Path("dist/framework-coverage-report-v1.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-bundle-schema", type=Path, default=CONTROL_BUNDLE_SCHEMA_PATH)
    parser.add_argument("--framework-report-schema", type=Path, default=FRAMEWORK_REPORT_SCHEMA_PATH)
    parser.add_argument("--control-bundle", type=Path, default=CONTROL_BUNDLE_PATH)
    parser.add_argument("--framework-report", type=Path, default=FRAMEWORK_REPORT_PATH)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_schema_file(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"missing schema: {path}"]
    schema = load_json(path)
    errors: list[str] = []
    try:
        Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        errors.append(f"{path}: invalid JSON Schema: {exc.message}")
    return schema, errors


def validate_payload(name: str, schema: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for error in validator.iter_errors(payload):
        location = ".".join(str(part) for part in error.absolute_path)
        if location:
            errors.append(f"{name}: {location}: {error.message}")
        else:
            errors.append(f"{name}: {error.message}")
    return errors


def semantic_bundle_checks(bundle: dict[str, Any], name: str) -> list[str]:
    errors: list[str] = []
    controls = bundle.get("controls", [])
    frameworks = bundle.get("frameworks", [])
    control_ids = bundle.get("control_ids", [])
    framework_ids = bundle.get("framework_ids", [])
    pattern_ids = bundle.get("pattern_ids", [])

    if bundle.get("control_count") != len(controls):
        errors.append(f"{name}: control_count does not match controls length")
    if bundle.get("framework_count") != len(frameworks):
        errors.append(f"{name}: framework_count does not match frameworks length")
    if sorted(control_ids) != sorted(control.get("id") for control in controls):
        errors.append(f"{name}: control_ids does not match control objects")
    if sorted(framework_ids) != sorted(framework.get("id") for framework in frameworks):
        errors.append(f"{name}: framework_ids does not match framework objects")

    derived_pattern_ids = sorted(
        {
            pattern_ref.get("id")
            for control in controls
            if isinstance(control, dict)
            for pattern_ref in control.get("pattern_refs", [])
            if isinstance(pattern_ref, dict) and isinstance(pattern_ref.get("id"), str)
        }
    )
    if bundle.get("pattern_coverage_count") != len(derived_pattern_ids):
        errors.append(f"{name}: pattern_coverage_count does not match unique pattern_refs")
    if sorted(pattern_ids) != derived_pattern_ids:
        errors.append(f"{name}: pattern_ids does not match unique pattern_refs")

    indexed_controls = {
        control.get("id"): control for control in controls if isinstance(control, dict) and isinstance(control.get("id"), str)
    }
    for framework in frameworks:
        if not isinstance(framework, dict):
            continue
        ids = framework.get("control_ids", [])
        refs = framework.get("controls", [])
        framework_id = framework.get("id", "<unknown>")
        if len(ids) != len(refs):
            errors.append(f"{name}: framework {framework_id} control_ids/controls length mismatch")
            continue
        ref_ids = [ref.get("id") for ref in refs if isinstance(ref, dict)]
        if ids != ref_ids:
            errors.append(f"{name}: framework {framework_id} controls do not align with control_ids order")
        missing = [control_id for control_id in ids if control_id not in indexed_controls]
        if missing:
            errors.append(f"{name}: framework {framework_id} references missing controls {missing}")
    return errors


def semantic_report_checks(report: dict[str, Any], name: str) -> list[str]:
    errors: list[str] = []
    frameworks = report.get("frameworks", [])
    if report.get("framework_count") != len(frameworks):
        errors.append(f"{name}: framework_count does not match frameworks length")

    derived_cross_family = sorted(
        framework.get("id")
        for framework in frameworks
        if isinstance(framework, dict)
        and isinstance(framework.get("id"), str)
        and len(framework.get("control_families", [])) > 1
    )
    if sorted(report.get("cross_family_framework_ids", [])) != derived_cross_family:
        errors.append(f"{name}: cross_family_framework_ids does not match framework rows")

    for framework in frameworks:
        if not isinstance(framework, dict):
            continue
        framework_id = framework.get("id", "<unknown>")
        control_ids = framework.get("control_ids", [])
        pattern_ids = framework.get("pattern_ids", [])
        if framework.get("control_count") != len(control_ids):
            errors.append(f"{name}: framework {framework_id} control_count does not match control_ids length")
        if framework.get("pattern_coverage_count") != len(pattern_ids):
            errors.append(f"{name}: framework {framework_id} pattern_coverage_count does not match pattern_ids length")
    return errors


def main() -> int:
    args = parse_args()

    control_schema, errors = validate_schema_file(args.control_bundle_schema)
    report_schema, report_errors = validate_schema_file(args.framework_report_schema)
    errors.extend(report_errors)

    if control_schema is None or report_schema is None:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    control_bundle = load_json(args.control_bundle)
    framework_report = load_json(args.framework_report)

    errors.extend(validate_payload(str(args.control_bundle), control_schema, control_bundle))
    errors.extend(validate_payload(str(args.framework_report), report_schema, framework_report))
    errors.extend(semantic_bundle_checks(control_bundle, str(args.control_bundle)))
    errors.extend(semantic_report_checks(framework_report, str(args.framework_report)))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Control/framework projection validation passed")
    print(f"  bundle schema: {args.control_bundle_schema}")
    print(f"  report schema: {args.framework_report_schema}")
    print(f"  bundle: {args.control_bundle}")
    print(f"  report: {args.framework_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

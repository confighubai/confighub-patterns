#!/usr/bin/env python3
"""Validate external evidence schema and test payloads.

This script:
1. Validates that external-evidence-v1.schema.json is valid JSON Schema
2. Validates test fixtures against the schema
3. Generates a sample valid payload for documentation

External evidence is ADVISORY ONLY and does not gate ConfigHub validation workflows.
The authoritative validation lane uses validate-unit/validate-space.
"""

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


SCHEMA_PATH = Path("schema/external-evidence-v1.schema.json")
FIXTURES_DIR = Path("test/fixtures/external-evidence")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate external evidence schema and fixtures"
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=SCHEMA_PATH,
        help="Path to external evidence schema",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=FIXTURES_DIR,
        help="Directory containing test fixtures",
    )
    parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="Generate a sample valid payload to stdout",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema_is_valid(schema: dict) -> list[str]:
    """Check that the schema itself is valid JSON Schema."""
    errors = []
    try:
        Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as e:
        errors.append(f"Invalid JSON Schema: {e.message}")
    return errors


def validate_payload(schema: dict, payload: dict, name: str) -> list[str]:
    """Validate a payload against the schema."""
    errors = []
    validator = Draft202012Validator(schema)
    for error in validator.iter_errors(payload):
        path = ".".join(str(p) for p in error.absolute_path)
        if path:
            errors.append(f"{name}: {path}: {error.message}")
        else:
            errors.append(f"{name}: {error.message}")
    return errors


def generate_sample_payload() -> dict:
    """Generate a sample valid external evidence payload."""
    return {
        "provenance": {
            "source": "cub-scan",
            "source_version": "0.4.0",
            "scan_time": "2026-04-02T15:00:00Z",
            "catalog_version": "risk-catalog-v1.json@abc123",
            "client_id": "ci-pipeline-prod",
            "environment": "production",
            "git_commit": "abc123def456",
            "git_repo": "https://github.com/org/repo",
            "git_branch": "main"
        },
        "association": {
            "space_id": "space-123",
            "unit_slug": "my-app"
        },
        "findings": [
            {
                "id": "CCVE-2025-3726",
                "name": "Deployment omits securityContext",
                "category": "SECURITY",
                "track": "misconfiguration",
                "detection_method": "native_rule",
                "severity": "warning",
                "confidence": "high",
                "tool": "workload",
                "resource": {
                    "kind": "Deployment",
                    "name": "api-server",
                    "namespace": "production"
                },
                "message": "Deployment omits pod and container securityContext settings",
                "remedy_type": "config_fix",
                "remedy_safety": "safe_auto",
                "remediation": {
                    "steps": [
                        "Add securityContext to pod spec",
                        "Add securityContext to container spec"
                    ],
                    "commands": [
                        "kubectl patch deployment api-server -n production -p '{...}'"
                    ]
                },
                "evidence_source": "native",
                "control_ids": ["CTRL-WH-0001"]
            }
        ],
        "summary": {
            "total": 1,
            "critical": 0,
            "warning": 1,
            "info": 0,
            "passed": False
        }
    }


def main() -> int:
    args = parse_args()

    if args.generate_sample:
        sample = generate_sample_payload()
        print(json.dumps(sample, indent=2))
        return 0

    errors: list[str] = []

    # Load schema
    if not args.schema.exists():
        print(f"ERROR: schema not found: {args.schema}")
        return 1

    schema = load_json(args.schema)

    # Validate schema is valid JSON Schema
    schema_errors = validate_schema_is_valid(schema)
    if schema_errors:
        for err in schema_errors:
            print(f"ERROR: {err}")
        return 1
    print(f"Schema validation passed: {args.schema}")

    # Validate fixtures if directory exists
    if args.fixtures.exists() and args.fixtures.is_dir():
        fixture_files = list(args.fixtures.glob("*.json"))
        for fixture_path in fixture_files:
            payload = load_json(fixture_path)
            fixture_errors = validate_payload(schema, payload, fixture_path.name)
            if fixture_errors:
                errors.extend(fixture_errors)
            else:
                print(f"Fixture validation passed: {fixture_path.name}")
    else:
        print(f"No fixtures directory found at {args.fixtures}, skipping fixture validation")

    # Validate sample payload
    sample = generate_sample_payload()
    sample_errors = validate_payload(schema, sample, "generated-sample")
    if sample_errors:
        errors.extend(sample_errors)
    else:
        print("Generated sample validation passed")

    # Validate empty findings case
    empty_payload = {
        "provenance": {
            "source": "cub-scan",
            "source_version": "0.4.0",
            "scan_time": "2026-04-02T15:00:00Z"
        },
        "findings": [],
        "summary": {
            "total": 0,
            "passed": True
        }
    }
    empty_errors = validate_payload(schema, empty_payload, "empty-findings")
    if empty_errors:
        errors.extend(empty_errors)
    else:
        print("Empty findings validation passed")

    if errors:
        print()
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    print()
    print("External evidence schema validation passed")
    print("  Note: External evidence is ADVISORY ONLY")
    print("  It does not gate ConfigHub validation workflows")
    return 0


if __name__ == "__main__":
    sys.exit(main())

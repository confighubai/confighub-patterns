#!/usr/bin/env python3
"""Validate risk/function link report against policy thresholds."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_REPORT_SCHEMA = "risk-function-links-v1"
EXPECTED_POLICY_SCHEMA = "risk-function-link-policy-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate risk/function link report policy")
    parser.add_argument(
        "--report",
        default="dist/risk-function-links-v1.json",
        help="Path to risk/function link report",
    )
    parser.add_argument(
        "--policy",
        default="quality/risk-function-link-thresholds-v1.json",
        help="Path to risk/function link policy",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    args = parse_args()
    report_path = Path(args.report)
    policy_path = Path(args.policy)

    errors: list[str] = []

    if not report_path.exists():
        _fail(errors, f"report not found: {report_path}")
    if not policy_path.exists():
        _fail(errors, f"policy not found: {policy_path}")
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    report = _load_json(report_path)
    policy = _load_json(policy_path)

    if not isinstance(report, dict):
        _fail(errors, "report must be object")
    if not isinstance(policy, dict):
        _fail(errors, "policy must be object")
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    report_schema = report.get("schema_version")
    if report_schema != EXPECTED_REPORT_SCHEMA:
        _fail(errors, f"report schema_version must be {EXPECTED_REPORT_SCHEMA!r}, got {report_schema!r}")

    policy_schema = policy.get("schema_version")
    if policy_schema != EXPECTED_POLICY_SCHEMA:
        _fail(errors, f"policy schema_version must be {EXPECTED_POLICY_SCHEMA!r}, got {policy_schema!r}")

    summary = report.get("summary")
    if not isinstance(summary, dict):
        _fail(errors, "report summary must be object")
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    # Metrics in report
    missing_fn_defs = _as_int(summary.get("missing_function_definitions"))
    missing_risks = _as_int(summary.get("function_declares_missing_risks"))
    mismatches = _as_int(summary.get("function_ccve_link_mismatches"))
    unreferenced = _as_int(summary.get("unreferenced_functions"))
    linked_risks = _as_int(summary.get("risks_with_function_ref"))
    total_functions = _as_int(summary.get("total_functions"))

    metric_names = {
        "missing_function_definitions": missing_fn_defs,
        "function_declares_missing_risks": missing_risks,
        "function_ccve_link_mismatches": mismatches,
        "unreferenced_functions": unreferenced,
        "risks_with_function_ref": linked_risks,
        "total_functions": total_functions,
    }
    for name, value in metric_names.items():
        if value is None:
            _fail(errors, f"summary.{name} must be integer")

    # Thresholds in policy
    max_missing_fn_defs = _as_int(policy.get("max_missing_function_definitions"))
    max_missing_risks = _as_int(policy.get("max_function_declares_missing_risks"))
    max_mismatches = _as_int(policy.get("max_function_ccve_link_mismatches"))
    max_unreferenced = _as_int(policy.get("max_unreferenced_functions"))
    min_linked_risks = _as_int(policy.get("min_risks_with_function_ref"))
    min_total_functions = _as_int(policy.get("min_total_functions"))

    policy_thresholds = {
        "max_missing_function_definitions": max_missing_fn_defs,
        "max_function_declares_missing_risks": max_missing_risks,
        "max_function_ccve_link_mismatches": max_mismatches,
        "max_unreferenced_functions": max_unreferenced,
        "min_risks_with_function_ref": min_linked_risks,
        "min_total_functions": min_total_functions,
    }
    for name, value in policy_thresholds.items():
        if value is None:
            _fail(errors, f"policy.{name} must be integer")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    assert missing_fn_defs is not None
    assert missing_risks is not None
    assert mismatches is not None
    assert unreferenced is not None
    assert linked_risks is not None
    assert total_functions is not None
    assert max_missing_fn_defs is not None
    assert max_missing_risks is not None
    assert max_mismatches is not None
    assert max_unreferenced is not None
    assert min_linked_risks is not None
    assert min_total_functions is not None

    if missing_fn_defs > max_missing_fn_defs:
        _fail(
            errors,
            "missing_function_definitions exceeded threshold: "
            f"{missing_fn_defs} > {max_missing_fn_defs}",
        )
    if missing_risks > max_missing_risks:
        _fail(
            errors,
            "function_declares_missing_risks exceeded threshold: "
            f"{missing_risks} > {max_missing_risks}",
        )
    if mismatches > max_mismatches:
        _fail(
            errors,
            "function_ccve_link_mismatches exceeded threshold: "
            f"{mismatches} > {max_mismatches}",
        )
    if unreferenced > max_unreferenced:
        _fail(
            errors,
            "unreferenced_functions exceeded threshold: "
            f"{unreferenced} > {max_unreferenced}",
        )
    if linked_risks < min_linked_risks:
        _fail(
            errors,
            "risks_with_function_ref below threshold: "
            f"{linked_risks} < {min_linked_risks}",
        )
    if total_functions < min_total_functions:
        _fail(
            errors,
            "total_functions below threshold: "
            f"{total_functions} < {min_total_functions}",
        )

    print("Risk/function link policy summary")
    print(f"  missing function definitions: {missing_fn_defs} (max {max_missing_fn_defs})")
    print(f"  missing risks in functions:   {missing_risks} (max {max_missing_risks})")
    print(f"  link mismatches:              {mismatches} (max {max_mismatches})")
    print(f"  unreferenced functions:       {unreferenced} (max {max_unreferenced})")
    print(f"  linked risks:                 {linked_risks} (min {min_linked_risks})")
    print(f"  total functions:              {total_functions} (min {min_total_functions})")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    print("Risk/function link policy validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

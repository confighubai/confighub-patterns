#!/usr/bin/env python3
"""Validate release severity decision packets against review-sample artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

EXPECTED_DECISION_SCHEMA = "severity-release-decision-v1"
EXPECTED_POLICY_SCHEMA = "severity-release-decision-policy-v1"
EXPECTED_REVIEW_SAMPLE_SCHEMA = "severity-review-sample-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate severity release decision packet")
    parser.add_argument(
        "--decision-file",
        required=True,
        help="Path to release severity decision packet JSON",
    )
    parser.add_argument(
        "--review-sample",
        default="dist/quality/severity-review-sample-v1.json",
        help="Path to generated severity review sample artifact",
    )
    parser.add_argument(
        "--policy",
        default="risks/quality/severity-release-decision-policy-v1.json",
        help="Path to severity release decision policy",
    )
    parser.add_argument(
        "--release-version",
        default="",
        help="Optional release version to enforce (for example v0.3.0-rc.1)",
    )
    return parser.parse_args()


def _load_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level object")
    return data


def _as_non_empty_string(value: Any) -> str:
    if isinstance(value, str):
        trimmed = value.strip()
        if trimmed:
            return trimmed
    return ""


def _path_non_empty(obj: dict[str, Any], path: str) -> bool:
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return False
        cur = cur.get(part)
    return _as_non_empty_string(cur) != ""


def main() -> int:
    args = parse_args()

    decision = _load_json(args.decision_file)
    review_sample = _load_json(args.review_sample)
    policy = _load_json(args.policy)

    issues: list[str] = []

    policy_schema = str(policy.get("schema_version", "")).strip()
    if policy_schema != EXPECTED_POLICY_SCHEMA:
        issues.append(
            f"{args.policy}: schema_version must be {EXPECTED_POLICY_SCHEMA}, got {policy_schema!r}"
        )

    decision_schema = str(decision.get("schema_version", "")).strip()
    if decision_schema != EXPECTED_DECISION_SCHEMA:
        issues.append(
            f"{args.decision_file}: schema_version must be {EXPECTED_DECISION_SCHEMA}, got {decision_schema!r}"
        )

    review_schema = str(review_sample.get("schema_version", "")).strip()
    if review_schema != EXPECTED_REVIEW_SAMPLE_SCHEMA:
        issues.append(
            f"{args.review_sample}: schema_version must be {EXPECTED_REVIEW_SAMPLE_SCHEMA}, got {review_schema!r}"
        )

    release_version = str(decision.get("release_version", "")).strip()
    release_pattern = str(
        policy.get("release_version_pattern", r"^v[0-9]+\.[0-9]+\.[0-9]+(?:-rc\.[0-9]+)?$")
    ).strip()
    if not release_version:
        issues.append("decision packet release_version is required")
    elif not re.fullmatch(release_pattern, release_version):
        issues.append(
            f"release_version {release_version!r} does not match policy pattern {release_pattern!r}"
        )
    if args.release_version and release_version and release_version != args.release_version:
        issues.append(
            f"release_version mismatch: decision packet has {release_version!r}, "
            f"expected {args.release_version!r}"
        )

    required_summary_fields = policy.get("required_summary_fields", [])
    if not isinstance(required_summary_fields, list):
        required_summary_fields = []
    summary = decision.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    for field in required_summary_fields:
        path = str(field).strip()
        if not path:
            continue
        if not _path_non_empty(summary, path):
            issues.append(f"summary.{path} must be present and non-empty")

    decisions = decision.get("decisions", [])
    if not isinstance(decisions, list):
        decisions = []
    min_decisions = int(policy.get("min_decisions", 1))
    if len(decisions) < min_decisions:
        issues.append(f"decision count {len(decisions)} is below minimum {min_decisions}")

    allowed_decisions = {
        str(v).strip().lower()
        for v in policy.get("allowed_decisions", ["accept", "adjust", "defer"])
        if str(v).strip()
    }
    required_decision_fields = policy.get("required_decision_fields", [])
    if not isinstance(required_decision_fields, list):
        required_decision_fields = []

    sample_items = review_sample.get("items", [])
    if not isinstance(sample_items, list):
        sample_items = []
    sample_ids = set()
    sample_launch_ids = set()
    for item in sample_items:
        if not isinstance(item, dict):
            continue
        ccve_id = str(item.get("id", "")).strip()
        if not ccve_id:
            continue
        sample_ids.add(ccve_id)
        if bool(item.get("launch_rule", False)):
            sample_launch_ids.add(ccve_id)

    decided_ids: set[str] = set()
    for i, row in enumerate(decisions):
        if not isinstance(row, dict):
            issues.append(f"decisions[{i}] must be an object")
            continue
        for field in required_decision_fields:
            key = str(field).strip()
            if not key:
                continue
            if _as_non_empty_string(row.get(key)) == "":
                issues.append(f"decisions[{i}].{key} must be present and non-empty")

        ccve_id = _as_non_empty_string(row.get("id"))
        if not ccve_id:
            continue
        if ccve_id in decided_ids:
            issues.append(f"duplicate decision id {ccve_id}")
        decided_ids.add(ccve_id)
        if sample_ids and ccve_id not in sample_ids:
            issues.append(f"decision id {ccve_id} is not present in review sample")

        decision_value = _as_non_empty_string(row.get("decision")).lower()
        if decision_value and decision_value not in allowed_decisions:
            issues.append(
                f"decisions[{i}].decision {decision_value!r} not in allowed set "
                f"{sorted(allowed_decisions)}"
            )

    if bool(policy.get("require_all_launch_items_decided", False)):
        missing_launch = sorted(sample_launch_ids - decided_ids)
        if missing_launch:
            issues.append(
                "missing decisions for launch-rule sample IDs: "
                + ", ".join(missing_launch[:20])
                + (" ..." if len(missing_launch) > 20 else "")
            )

    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1

    print("Severity release decision summary")
    print(f"  release version:     {release_version}")
    print(f"  sample items:        {len(sample_ids)}")
    print(f"  launch sample items: {len(sample_launch_ids)}")
    print(f"  decisions:           {len(decisions)}")
    print("Severity release decision validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

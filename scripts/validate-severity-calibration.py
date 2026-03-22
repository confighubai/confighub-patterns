#!/usr/bin/env python3
"""Validate severity calibration guardrails against catalog and launch policy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_POLICY_SCHEMAS = {
    "severity-calibration-policy-v1",
    "severity-calibration-policy-v2",
}
SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate severity calibration guardrails")
    parser.add_argument(
        "--catalog",
        default="dist/risk-catalog-v1.json",
        help="Path to normalized risk catalog",
    )
    parser.add_argument(
        "--launch-policy",
        default="risks/quality/launch-rules-v1.json",
        help="Path to launch quality rules policy",
    )
    parser.add_argument(
        "--policy",
        default="risks/quality/severity-calibration-policy-v2.json",
        help="Path to severity calibration policy",
    )
    parser.add_argument(
        "--baseline",
        default="",
        help="Optional baseline report/baseline JSON for distribution delta output",
    )
    parser.add_argument(
        "--report-out",
        default="",
        help="Optional output path for severity calibration report JSON",
    )
    return parser.parse_args()


def _load_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level object")
    return data


def _norm_severity(raw: str) -> str:
    value = raw.strip().lower()
    if value in {"critical", "high"}:
        return "critical"
    if value in {"warning", "warn", "medium"}:
        return "warning"
    if value in {"info", "informational", "low"}:
        return "info"
    return "warning"


def _bucket_rank(bucket: str) -> int:
    return SEVERITY_ORDER.get(bucket.strip().lower(), 1)


def _get_by_path(obj: Any, path: str) -> Any:
    cur = obj
    for segment in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(segment)
        else:
            return None
    return cur


def _has_non_empty_path(obj: dict[str, Any], path: str) -> bool:
    value = _get_by_path(obj, path)
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _inc3(buckets: dict[str, int], bucket: str) -> None:
    if bucket not in buckets:
        buckets[bucket] = 0
    buckets[bucket] += 1


def _normalize_counts(counts: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in counts.items():
        if isinstance(value, dict):
            out[key] = _normalize_counts(value)
        else:
            out[key] = int(value)
    return out


def _diff_counts(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    keys = sorted(set(current.keys()) | set(baseline.keys()))
    out: dict[str, Any] = {}
    for key in keys:
        left = current.get(key)
        right = baseline.get(key)
        if isinstance(left, dict) or isinstance(right, dict):
            left_dict = left if isinstance(left, dict) else {}
            right_dict = right if isinstance(right, dict) else {}
            out[key] = _diff_counts(left_dict, right_dict)
            continue
        left_val = int(left or 0)
        right_val = int(right or 0)
        out[key] = left_val - right_val
    return out


def main() -> int:
    args = parse_args()

    catalog = _load_json(args.catalog)
    launch_policy = _load_json(args.launch_policy)
    policy = _load_json(args.policy)

    schema = str(policy.get("schema_version", "")).strip()
    if schema not in EXPECTED_POLICY_SCHEMAS:
        print(
            "ERROR: "
            f"{args.policy}: schema_version must be one of {sorted(EXPECTED_POLICY_SCHEMAS)}, got {schema!r}"
        )
        return 1

    entries_raw = catalog.get("entries", [])
    if not isinstance(entries_raw, list):
        print(f"ERROR: {args.catalog}: entries must be an array")
        return 1

    launch_rules = launch_policy.get("rules", [])
    if not isinstance(launch_rules, list):
        print(f"ERROR: {args.launch_policy}: rules must be an array")
        return 1

    entries: dict[str, dict[str, Any]] = {}
    for item in entries_raw:
        if not isinstance(item, dict):
            continue
        ccve_id = str(item.get("id", "")).strip()
        if ccve_id:
            entries[ccve_id] = item

    launch_ids = []
    for rule in launch_rules:
        if not isinstance(rule, dict):
            continue
        ccve_id = str(rule.get("id", "")).strip()
        if ccve_id:
            launch_ids.append(ccve_id)

    max_launch_info = int(policy.get("max_launch_info", 0))
    allow_launch_info = {str(v).strip() for v in policy.get("allow_launch_info_ids", [])}
    forbid_advisory_critical = bool(policy.get("forbid_advisory_critical", True))
    max_security_info = int(policy.get("max_security_info", 0))
    allow_security_info = {str(v).strip() for v in policy.get("allow_security_info_ids", [])}

    category_constraints_raw = policy.get("category_bucket_constraints", [])
    category_constraints: list[dict[str, Any]] = []
    if isinstance(category_constraints_raw, list):
        for item in category_constraints_raw:
            if isinstance(item, dict):
                category_constraints.append(item)

    require_launch_rationale = bool(policy.get("require_launch_rationale", False))
    launch_rationale_paths = policy.get("launch_rationale_paths", ["references"])
    if not isinstance(launch_rationale_paths, list):
        launch_rationale_paths = ["references"]
    launch_rationale_paths = [str(v).strip() for v in launch_rationale_paths if str(v).strip()]

    issues: list[str] = []
    launch_info_ids: list[str] = []
    advisory_critical_ids: list[str] = []
    security_info_ids: list[str] = []
    severity_mismatch_ids: list[str] = []
    missing_launch_ids: list[str] = []
    launch_rationale_missing_ids: list[str] = []
    category_constraint_violation_ids: list[str] = []

    distribution = {
        "by_bucket": {"critical": 0, "warning": 0, "info": 0},
        "by_track": {},
        "by_category": {},
    }

    for ccve_id in launch_ids:
        entry = entries.get(ccve_id)
        if entry is None:
            missing_launch_ids.append(ccve_id)
            continue
        severity = entry.get("severity", {})
        if isinstance(severity, dict):
            bucket = _norm_severity(str(severity.get("bucket", "") or severity.get("raw", "")))
            if bucket == "info":
                launch_info_ids.append(ccve_id)

        if require_launch_rationale:
            has_rationale = any(_has_non_empty_path(entry, p) for p in launch_rationale_paths)
            if not has_rationale:
                launch_rationale_missing_ids.append(ccve_id)

    for ccve_id, entry in entries.items():
        severity = entry.get("severity", {})
        if not isinstance(severity, dict):
            continue
        raw = str(severity.get("raw", "")).strip().lower()
        bucket = str(severity.get("bucket", "")).strip().lower()

        normalized = _norm_severity(raw)
        normalized_bucket = _norm_severity(bucket or raw)

        if bucket and bucket != normalized:
            severity_mismatch_ids.append(ccve_id)

        track = str(entry.get("track", "")).strip().lower() or "unknown"
        category = str(entry.get("category", "")).strip().upper() or "UNKNOWN"

        _inc3(distribution["by_bucket"], normalized_bucket)

        track_buckets = distribution["by_track"].setdefault(track, {"critical": 0, "warning": 0, "info": 0})
        _inc3(track_buckets, normalized_bucket)

        category_buckets = distribution["by_category"].setdefault(
            category, {"critical": 0, "warning": 0, "info": 0}
        )
        _inc3(category_buckets, normalized_bucket)

        if forbid_advisory_critical and track == "advisory" and normalized_bucket == "critical":
            advisory_critical_ids.append(ccve_id)
        if category == "SECURITY" and normalized_bucket == "info":
            security_info_ids.append(ccve_id)

        for constraint in category_constraints:
            target = str(constraint.get("category", "")).strip().upper()
            if target != category:
                continue
            allowed_ids = {str(v).strip() for v in constraint.get("allow_ids", [])}
            if ccve_id in allowed_ids:
                continue
            min_bucket = str(constraint.get("min_bucket", "info")).strip().lower() or "info"
            max_bucket = str(constraint.get("max_bucket", "critical")).strip().lower() or "critical"
            rank = _bucket_rank(normalized_bucket)
            if rank < _bucket_rank(min_bucket) or rank > _bucket_rank(max_bucket):
                category_constraint_violation_ids.append(ccve_id)

    unexpected_launch_info = sorted([i for i in launch_info_ids if i not in allow_launch_info])
    unexpected_security_info = sorted([i for i in security_info_ids if i not in allow_security_info])

    if missing_launch_ids:
        issues.append(f"launch rules missing from catalog: {missing_launch_ids[:10]}")
    if severity_mismatch_ids:
        issues.append(f"severity raw/bucket mismatch: {severity_mismatch_ids[:10]}")
    if len(launch_info_ids) > max_launch_info:
        issues.append(
            f"launch info findings {len(launch_info_ids)} exceed max_launch_info={max_launch_info}"
        )
    if unexpected_launch_info:
        issues.append(f"launch info IDs outside allowlist: {unexpected_launch_info[:10]}")
    if advisory_critical_ids:
        issues.append(f"advisory track contains critical severity IDs: {advisory_critical_ids[:10]}")
    if len(security_info_ids) > max_security_info:
        issues.append(
            f"security info findings {len(security_info_ids)} exceed max_security_info={max_security_info}"
        )
    if unexpected_security_info:
        issues.append(f"security info IDs outside allowlist: {unexpected_security_info[:10]}")
    if category_constraint_violation_ids:
        issues.append(
            "category severity constraint violations: "
            f"{sorted(category_constraint_violation_ids)[:10]}"
        )
    if launch_rationale_missing_ids:
        issues.append(
            "launch rules missing severity rationale evidence: "
            f"{sorted(launch_rationale_missing_ids)[:10]}"
        )

    report: dict[str, Any] = {
        "schema_version": "severity-calibration-report-v1",
        "catalog_entries": len(entries),
        "launch_rules": len(launch_ids),
        "summary": {
            "launch_info_findings": len(launch_info_ids),
            "advisory_critical_findings": len(advisory_critical_ids),
            "security_info_findings": len(security_info_ids),
            "severity_raw_bucket_mismatch": len(severity_mismatch_ids),
            "missing_launch_rules": len(missing_launch_ids),
            "category_constraint_violations": len(category_constraint_violation_ids),
            "launch_rationale_missing": len(launch_rationale_missing_ids),
        },
        "distribution": _normalize_counts(distribution),
        "violations": {
            "missing_launch_ids": sorted(missing_launch_ids),
            "launch_info_ids": sorted(launch_info_ids),
            "unexpected_launch_info_ids": unexpected_launch_info,
            "advisory_critical_ids": sorted(advisory_critical_ids),
            "security_info_ids": sorted(security_info_ids),
            "unexpected_security_info_ids": unexpected_security_info,
            "severity_mismatch_ids": sorted(severity_mismatch_ids),
            "category_constraint_violation_ids": sorted(category_constraint_violation_ids),
            "launch_rationale_missing_ids": sorted(launch_rationale_missing_ids),
        },
    }

    baseline_data: dict[str, Any] = {}
    if args.baseline:
        baseline_path = Path(args.baseline)
        if baseline_path.exists():
            loaded = _load_json(args.baseline)
            if loaded.get("schema_version") == "severity-calibration-report-v1":
                baseline_data = loaded.get("distribution", {})
            else:
                baseline_data = loaded.get("distribution", {})
        else:
            print(f"WARN: baseline file not found: {args.baseline}")

    if isinstance(baseline_data, dict) and baseline_data:
        report["delta"] = _diff_counts(
            report["distribution"],
            _normalize_counts(baseline_data),
        )

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("Severity calibration summary")
    print(f"  catalog entries:               {len(entries)}")
    print(f"  launch rules:                 {len(launch_ids)}")
    print(f"  launch info findings:         {len(launch_info_ids)} (max {max_launch_info})")
    print(f"  advisory critical findings:   {len(advisory_critical_ids)}")
    print(f"  security info findings:       {len(security_info_ids)} (max {max_security_info})")
    print(f"  severity raw/bucket mismatch: {len(severity_mismatch_ids)}")
    print(f"  category constraint violations:{len(category_constraint_violation_ids)}")
    print(f"  launch rationale missing:     {len(launch_rationale_missing_ids)}")
    if args.report_out:
        print(f"  report:                       {args.report_out}")

    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1

    print("Severity calibration policy validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build deterministic severity review sample packet for manual calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_POLICY_SCHEMA = "severity-review-sample-policy-v1"
SEVERITY_ORDER = {"critical": 3, "warning": 2, "info": 1}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build severity review sample packet")
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
        default="risks/quality/severity-review-sample-policy-v1.json",
        help="Path to severity review sample policy",
    )
    parser.add_argument(
        "--out",
        default="dist/quality/severity-review-sample-v1.json",
        help="Output path for review sample artifact",
    )
    return parser.parse_args()


def _load_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level object")
    return data


def _norm_severity(raw_bucket: str, raw_value: str) -> str:
    bucket = raw_bucket.strip().lower()
    if bucket in {"critical", "warning", "info"}:
        return bucket
    value = raw_value.strip().lower()
    if value in {"critical", "high"}:
        return "critical"
    if value in {"warning", "warn", "medium"}:
        return "warning"
    if value in {"info", "informational", "low"}:
        return "info"
    return "warning"


def _stable_hash(seed: str, value: str) -> int:
    digest = hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _get_by_path(obj: Any, path: str) -> Any:
    cur = obj
    for segment in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(segment)
        else:
            return None
    return cur


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _category_rank(category: str, priorities: list[str]) -> int:
    try:
        return priorities.index(category)
    except ValueError:
        return len(priorities)


def main() -> int:
    args = parse_args()

    catalog = _load_json(args.catalog)
    launch = _load_json(args.launch_policy)
    policy = _load_json(args.policy)

    schema = str(policy.get("schema_version", "")).strip()
    if schema != EXPECTED_POLICY_SCHEMA:
        print(
            f"ERROR: {args.policy}: schema_version must be {EXPECTED_POLICY_SCHEMA}, got {schema!r}"
        )
        return 1

    entries_raw = catalog.get("entries", [])
    if not isinstance(entries_raw, list):
        print(f"ERROR: {args.catalog}: entries must be an array")
        return 1

    launch_rules = launch.get("rules", [])
    if not isinstance(launch_rules, list):
        print(f"ERROR: {args.launch_policy}: rules must be an array")
        return 1

    seed = str(policy.get("seed", "severity-review")).strip()
    sample_size = int(policy.get("sample_size", 24))
    launch_sample_size = int(policy.get("launch_rule_sample_size", 8))

    per_severity_min_raw = policy.get("per_severity_min", {})
    per_severity_min: dict[str, int] = {}
    if isinstance(per_severity_min_raw, dict):
        for key, value in per_severity_min_raw.items():
            per_severity_min[str(key).strip().lower()] = int(value)

    per_category_max_raw = policy.get("per_category_max", {})
    per_category_max: dict[str, int] = {}
    if isinstance(per_category_max_raw, dict):
        for key, value in per_category_max_raw.items():
            per_category_max[str(key).strip().upper()] = int(value)

    category_priority = policy.get("category_priority", ["SECURITY", "CONFIG", "STATE"])
    if not isinstance(category_priority, list):
        category_priority = ["SECURITY", "CONFIG", "STATE"]
    category_priority = [str(v).strip().upper() for v in category_priority if str(v).strip()]

    required_paths = policy.get("required_rationale_paths", ["references"])
    if not isinstance(required_paths, list):
        required_paths = ["references"]
    required_paths = [str(v).strip() for v in required_paths if str(v).strip()]

    launch_ids = set()
    for rule in launch_rules:
        if not isinstance(rule, dict):
            continue
        ccve_id = str(rule.get("id", "")).strip()
        if ccve_id:
            launch_ids.add(ccve_id)

    candidates = []
    for entry in entries_raw:
        if not isinstance(entry, dict):
            continue
        ccve_id = str(entry.get("id", "")).strip()
        if not ccve_id:
            continue
        severity = entry.get("severity", {})
        if not isinstance(severity, dict):
            severity = {}
        severity_raw = str(severity.get("raw", "")).strip().lower()
        severity_bucket_raw = str(severity.get("bucket", "")).strip().lower()
        severity_bucket = _norm_severity(severity_bucket_raw, severity_raw)
        category = str(entry.get("category", "UNKNOWN")).strip().upper() or "UNKNOWN"
        track = str(entry.get("track", "")).strip().lower() or "misconfiguration"
        metadata = entry.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        references = entry.get("references", [])
        references_count = len(references) if isinstance(references, list) else 0

        candidates.append(
            {
                "id": ccve_id,
                "name": str(entry.get("name", "")).strip(),
                "category": category,
                "track": track,
                "severity_bucket": severity_bucket,
                "severity_raw": severity_raw,
                "source_file": str(metadata.get("file", "")).strip(),
                "references_count": references_count,
                "launch_rule": ccve_id in launch_ids,
                "_entry": entry,
                "_hash": _stable_hash(seed, ccve_id),
            }
        )

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    severity_counts: dict[str, int] = {"critical": 0, "warning": 0, "info": 0}
    category_counts: dict[str, int] = {}

    def can_add(item: dict[str, Any], ignore_category_limits: bool = False) -> bool:
        if item["id"] in selected_ids:
            return False
        category = str(item["category"])
        if not ignore_category_limits and category in per_category_max:
            if category_counts.get(category, 0) >= per_category_max[category]:
                return False
        return True

    def add_item(item: dict[str, Any]) -> None:
        selected.append(item)
        selected_ids.add(item["id"])
        sev = item["severity_bucket"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        category = item["category"]
        category_counts[category] = category_counts.get(category, 0) + 1

    launch_candidates = [c for c in candidates if c["launch_rule"]]
    launch_candidates.sort(key=lambda c: c["_hash"])
    launch_selected = 0
    for item in launch_candidates:
        if launch_selected >= launch_sample_size or len(selected) >= sample_size:
            break
        if not can_add(item, ignore_category_limits=True):
            continue
        add_item(item)
        launch_selected += 1

    for severity in ["critical", "warning", "info"]:
        required_min = per_severity_min.get(severity, 0)
        if required_min <= 0:
            continue
        pool = [c for c in candidates if c["severity_bucket"] == severity and c["id"] not in selected_ids]
        pool.sort(
            key=lambda c: (
                _category_rank(c["category"], category_priority),
                c["_hash"],
            )
        )
        for item in pool:
            if severity_counts.get(severity, 0) >= required_min or len(selected) >= sample_size:
                break
            if not can_add(item):
                continue
            add_item(item)

    ranked = sorted(
        [c for c in candidates if c["id"] not in selected_ids],
        key=lambda c: (
            -SEVERITY_ORDER.get(c["severity_bucket"], 2),
            _category_rank(c["category"], category_priority),
            c["_hash"],
        ),
    )

    for item in ranked:
        if len(selected) >= sample_size:
            break
        if not can_add(item):
            continue
        add_item(item)

    if len(selected) < sample_size:
        for item in ranked:
            if len(selected) >= sample_size:
                break
            if not can_add(item, ignore_category_limits=True):
                continue
            add_item(item)

    out_items: list[dict[str, Any]] = []
    rationale_ok = 0
    for item in selected:
        entry = item.pop("_entry")
        item.pop("_hash", None)
        missing_paths = []
        for path in required_paths:
            if not _is_non_empty(_get_by_path(entry, path)):
                missing_paths.append(path)
        has_rationale = len(missing_paths) == 0
        if has_rationale:
            rationale_ok += 1
        out_items.append(
            {
                **item,
                "rationale": {
                    "required_paths": required_paths,
                    "missing_paths": missing_paths,
                    "has_required_evidence": has_rationale,
                },
            }
        )

    out_items.sort(key=lambda i: i["id"])

    report = {
        "schema_version": "severity-review-sample-v1",
        "policy_schema": EXPECTED_POLICY_SCHEMA,
        "seed": seed,
        "summary": {
            "catalog_entries": len(candidates),
            "launch_rules": len(launch_ids),
            "selected_count": len(out_items),
            "launch_selected_count": sum(1 for i in out_items if i.get("launch_rule")),
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "rationale_complete_count": rationale_ok,
        },
        "items": out_items,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("Severity review sample summary")
    print(f"  catalog entries:        {len(candidates)}")
    print(f"  launch rules:          {len(launch_ids)}")
    print(f"  selected sample size:  {len(out_items)}")
    print(f"  launch in sample:      {sum(1 for i in out_items if i.get('launch_rule'))}")
    print(f"  rationale complete:    {rationale_ok}/{len(out_items)}")
    print(f"  output:                {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

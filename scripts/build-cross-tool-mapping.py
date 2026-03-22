#!/usr/bin/env python3
"""Build cross-tool mapping artifact and enforce drift/policy gates."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
from typing import Any


POLICY_SCHEMA = "cross-tool-mapping-policy-v1"
OUTPUT_SCHEMA = "cross-tool-mapping-v1"
CATALOG_SCHEMA = "risk-catalog-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build cross-tool mapping artifact")
    parser.add_argument(
        "--catalog",
        default="dist/risk-catalog-v1.json",
        help="Catalog path",
    )
    parser.add_argument(
        "--policy",
        default="quality/cross-tool-mapping-policy-v1.json",
        help="Cross-tool mapping policy path",
    )
    parser.add_argument(
        "--output",
        default="dist/quality/cross-tool-mapping-v1.json",
        help="Output artifact path",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check mode: fail if output differs from on-disk file",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level object")
    return data


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _as_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return int(text)
        except ValueError:
            return default
    return default


def _json_bytes(doc: Any) -> bytes:
    return (json.dumps(doc, indent=2) + "\n").encode("utf-8")


def _write_or_check(path: Path, content: bytes, check: bool) -> tuple[bool, bool]:
    if path.exists():
        current = path.read_bytes()
        matches = current == content
    else:
        matches = False

    if check:
        return matches, not matches

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return True, not matches


def _resolve_policy_path(raw: str, policy_path: Path) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    rel_to_policy = (policy_path.parent / candidate).resolve()
    if rel_to_policy.exists():
        return rel_to_policy
    return candidate.resolve()


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _validate_policy(policy: dict[str, Any], policy_path: Path) -> tuple[list[dict[str, Any]], dict[str, int], int]:
    if _norm_text(policy.get("schema_version")) != POLICY_SCHEMA:
        raise ValueError(f"{policy_path}: schema_version must be {POLICY_SCHEMA!r}")

    tool_mappings = policy.get("tool_mappings")
    if not isinstance(tool_mappings, list) or not tool_mappings:
        raise ValueError(f"{policy_path}: tool_mappings must be a non-empty list")

    normalized_tools: list[dict[str, Any]] = []
    for i, row in enumerate(tool_mappings):
        if not isinstance(row, dict):
            raise ValueError(f"{policy_path}: tool_mappings[{i}] must be an object")
        tool = _norm_text(row.get("tool")).lower()
        path = _norm_text(row.get("path"))
        schema_version = _norm_text(row.get("schema_version"))
        id_fields_raw = row.get("external_id_fields")
        if not tool:
            raise ValueError(f"{policy_path}: tool_mappings[{i}].tool is required")
        if not path:
            raise ValueError(f"{policy_path}: tool_mappings[{i}].path is required")
        if not schema_version:
            raise ValueError(f"{policy_path}: tool_mappings[{i}].schema_version is required")
        if not isinstance(id_fields_raw, list) or not id_fields_raw:
            raise ValueError(
                f"{policy_path}: tool_mappings[{i}].external_id_fields must be a non-empty list"
            )
        id_fields = [_norm_text(v) for v in id_fields_raw if _norm_text(v)]
        if not id_fields:
            raise ValueError(
                f"{policy_path}: tool_mappings[{i}].external_id_fields must contain non-empty keys"
            )

        normalized_tools.append(
            {
                "tool": tool,
                "path": _resolve_policy_path(path, policy_path),
                "schema_version": schema_version,
                "external_id_fields": id_fields,
            }
        )

    minimums_raw = policy.get("min_mappings_by_tool")
    if not isinstance(minimums_raw, dict):
        raise ValueError(f"{policy_path}: min_mappings_by_tool must be an object")
    minimums: dict[str, int] = {}
    for tool, value in minimums_raw.items():
        tool_name = _norm_text(tool).lower()
        if not tool_name:
            continue
        minimums[tool_name] = _as_int(value, 0)

    max_missing = _as_int(policy.get("max_missing_catalog_refs"), -1)
    if max_missing < 0:
        raise ValueError(f"{policy_path}: max_missing_catalog_refs must be >= 0")

    return normalized_tools, minimums, max_missing


def main() -> int:
    args = parse_args()
    root = Path.cwd()
    catalog_path = Path(args.catalog)
    policy_path = Path(args.policy)
    output_path = Path(args.output)

    try:
        catalog = _load_json(catalog_path)
        policy = _load_json(policy_path)
        tool_configs, minimums, max_missing = _validate_policy(policy, policy_path)
    except (OSError, ValueError, json.JSONDecodeError) as err:
        print(f"ERROR: {err}")
        return 1

    if _norm_text(catalog.get("schema_version")) != CATALOG_SCHEMA:
        print(f"ERROR: {catalog_path}: schema_version must be {CATALOG_SCHEMA!r}")
        return 1

    entries = catalog.get("entries")
    if not isinstance(entries, list):
        print(f"ERROR: {catalog_path}: entries must be a list")
        return 1
    catalog_ids = {_norm_text(row.get("id")) for row in entries if isinstance(row, dict)}
    catalog_ids.discard("")

    mappings_out: list[dict[str, Any]] = []
    tool_summary: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    missing_refs: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for config in tool_configs:
        tool = config["tool"]
        mapping_path: Path = config["path"]
        expected_schema = config["schema_version"]
        id_fields = config["external_id_fields"]

        try:
            doc = _load_json(mapping_path)
        except (OSError, ValueError, json.JSONDecodeError) as err:
            errors.append(f"{tool}: failed to load {mapping_path}: {err}")
            continue

        schema_version = _norm_text(doc.get("schema_version"))
        if schema_version != expected_schema:
            errors.append(
                f"{tool}: {mapping_path} schema_version must be {expected_schema!r}, got {schema_version!r}"
            )
            continue

        rows = doc.get("mappings")
        if not isinstance(rows, list):
            errors.append(f"{tool}: {mapping_path} mappings must be a list")
            continue

        tool_info = tool_summary.setdefault(
            tool,
            {
                "path": _display_path(mapping_path, root),
                "mappings": 0,
                "unique_ccve_ids": 0,
                "missing_catalog_refs": 0,
            },
        )
        tool_ccves: set[str] = set()
        seen_tool_external: set[str] = set()

        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{tool}: mappings[{i}] must be an object")
                continue
            ccve_id = _norm_text(row.get("ccve_id"))
            if not ccve_id:
                errors.append(f"{tool}: mappings[{i}].ccve_id is required")
                continue

            external_parts = []
            missing_id_part = False
            for field in id_fields:
                value = _norm_text(row.get(field))
                if not value:
                    errors.append(f"{tool}: mappings[{i}].{field} is required")
                    missing_id_part = True
                    break
                external_parts.append(value)
            if missing_id_part:
                continue
            external_id = "|".join(external_parts)

            tool_key = f"{tool}:{external_id}"
            if tool_key in seen_tool_external:
                errors.append(f"{tool}: duplicate external mapping id {external_id!r}")
                continue
            seen_tool_external.add(tool_key)
            if tool_key in seen_keys:
                errors.append(f"duplicate mapping key {tool_key!r}")
                continue
            seen_keys.add(tool_key)

            if ccve_id not in catalog_ids:
                tool_info["missing_catalog_refs"] += 1
                missing_refs.append(
                    {
                        "tool": tool,
                        "external_id": external_id,
                        "ccve_id": ccve_id,
                    }
                )

            mappings_out.append(
                {
                    "tool": tool,
                    "external_id": external_id,
                    "ccve_id": ccve_id,
                    "category": _norm_text(row.get("category")),
                    "track": _norm_text(row.get("track")),
                    "source_file": _display_path(mapping_path, root),
                }
            )
            tool_ccves.add(ccve_id)
            tool_info["mappings"] += 1

        tool_info["unique_ccve_ids"] = len(tool_ccves)

    mappings_out.sort(key=lambda row: (row["tool"], row["external_id"], row["ccve_id"]))
    missing_refs.sort(key=lambda row: (row["tool"], row["external_id"], row["ccve_id"]))

    policy_failures: list[str] = []
    for tool, minimum in minimums.items():
        observed = int(tool_summary.get(tool, {}).get("mappings", 0))
        if observed < minimum:
            policy_failures.append(f"{tool}: mappings {observed} below minimum {minimum}")

    if len(missing_refs) > max_missing:
        policy_failures.append(
            f"missing catalog refs {len(missing_refs)} exceed max {max_missing}"
        )

    report = {
        "schema_version": OUTPUT_SCHEMA,
        "policy_schema_version": POLICY_SCHEMA,
        "catalog_schema_version": CATALOG_SCHEMA,
        "summary": {
            "tools": len(tool_summary),
            "total_mappings": len(mappings_out),
            "mapped_ccve_ids": len({row["ccve_id"] for row in mappings_out}),
            "missing_catalog_refs": len(missing_refs),
            "policy_failures": len(policy_failures),
            "errors": len(errors),
        },
        "tools": {tool: tool_summary[tool] for tool in sorted(tool_summary)},
        "mappings": mappings_out,
        "missing_catalog_refs": missing_refs,
        "policy_failure_messages": policy_failures,
        "error_messages": errors,
    }

    out_bytes = _json_bytes(report)
    matches, _ = _write_or_check(output_path, out_bytes, args.check)

    print("Cross-tool mapping summary")
    print(f"  tools:               {report['summary']['tools']}")
    print(f"  total mappings:      {report['summary']['total_mappings']}")
    print(f"  mapped CCVE IDs:     {report['summary']['mapped_ccve_ids']}")
    print(f"  missing catalog refs:{report['summary']['missing_catalog_refs']}")
    print(f"  policy failures:     {report['summary']['policy_failures']}")
    print(f"  errors:              {report['summary']['errors']}")

    if args.check and not matches:
        diff_lines = []
        if output_path.exists():
            current = output_path.read_text(encoding="utf-8")
            diff_lines = list(
                difflib.unified_diff(
                    current.splitlines(keepends=True),
                    out_bytes.decode("utf-8").splitlines(keepends=True),
                    fromfile=str(output_path),
                    tofile="generated",
                )
            )
        print(f"CHECK FAILED: {output_path} is out of date")
        if diff_lines:
            print("".join(diff_lines[:200]), end="")
        return 1

    if not args.check:
        print(f"Wrote {output_path}")

    if policy_failures:
        for msg in policy_failures:
            print(f"ERROR: {msg}")
    if errors:
        for msg in errors:
            print(f"ERROR: {msg}")

    if policy_failures or errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

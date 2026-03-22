#!/usr/bin/env python3
"""
Build a normalized cross-link report between CCVE risks and remedy functions.

Outputs:
  1. dist/risk-function-links-v1.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


TRACK_VALUES = {"misconfiguration", "advisory"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build risk/function cross-link report")
    parser.add_argument("--risks-dir", default="risks", help="Directory containing CCVE YAML files")
    parser.add_argument("--functions-dir", default="functions", help="Directory containing function YAML files")
    parser.add_argument(
        "--output",
        default="dist/risk-function-links-v1.json",
        help="Output report path",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check mode: fail if generated output differs from on-disk file",
    )
    return parser.parse_args()


def _norm(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    text = str(value).strip()
    return text if text else None


def _track_for(category: str, explicit_track: str | None) -> str:
    if explicit_track:
        normalized = explicit_track.lower()
        if normalized in TRACK_VALUES:
            return normalized
    if category == "OVER_PROVISION":
        return "advisory"
    return "misconfiguration"


def _json_bytes(doc: Any) -> bytes:
    return (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _write_or_check(path: Path, content: bytes, check: bool) -> tuple[bool, bool]:
    """
    Returns:
      (matches_on_disk, changed_or_would_change)
    """
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


def _as_sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _display_path(path: Path, root_parent: Path) -> str:
    try:
        return path.resolve().relative_to(root_parent.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_risks(risks_dir: Path) -> dict[str, dict[str, Any]]:
    risks: dict[str, dict[str, Any]] = {}
    root_parent = risks_dir.parent
    for path in sorted(risks_dir.glob("CCVE-2025-*.yaml")):
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if not isinstance(raw, dict):
            continue

        risk_id = _norm(raw.get("id")) or path.stem
        category = (_norm(raw.get("category")) or "CONFIG").upper()
        track = _track_for(category, _norm(raw.get("track")))
        remedy = raw.get("remedy")
        remedy_obj = remedy if isinstance(remedy, dict) else {}
        remedy_function = _norm(remedy_obj.get("function"))
        remedy_type = _norm(remedy_obj.get("type"))

        risks[risk_id] = {
            "id": risk_id,
            "category": category,
            "track": track,
            "remedy_function": remedy_function,
            "remedy_type": remedy_type,
            "source_path": _display_path(path, root_parent),
        }
    return risks


def _load_functions(functions_dir: Path) -> dict[str, dict[str, Any]]:
    funcs: dict[str, dict[str, Any]] = {}
    root_parent = functions_dir.parent
    for path in sorted(functions_dir.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if not isinstance(raw, dict):
            continue

        function_id = _norm(raw.get("id")) or path.stem
        ccves_raw = raw.get("ccves")
        if isinstance(ccves_raw, list):
            ccves = [_norm(item) for item in ccves_raw]
        elif ccves_raw is None:
            ccve_single = _norm(raw.get("ccve"))
            ccves = [ccve_single] if ccve_single else []
        else:
            ccve_single = _norm(ccves_raw)
            ccves = [ccve_single] if ccve_single else []

        funcs[function_id] = {
            "id": function_id,
            "ccves": sorted({ccve for ccve in ccves if ccve}),
            "source_path": _display_path(path, root_parent),
        }
    return funcs


def main() -> int:
    args = parse_args()
    risks_dir = Path(args.risks_dir)
    functions_dir = Path(args.functions_dir)
    output_path = Path(args.output)

    if not risks_dir.exists():
        print(f"ERROR: risks directory not found: {risks_dir}")
        return 1
    if not functions_dir.exists():
        print(f"ERROR: functions directory not found: {functions_dir}")
        return 1

    risks = _load_risks(risks_dir)
    functions = _load_functions(functions_dir)

    track_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    remedy_type_counts: Counter[str] = Counter()
    risk_to_function: list[dict[str, Any]] = []
    function_to_risks: dict[str, list[str]] = {fid: [] for fid in functions}
    missing_function_defs: list[dict[str, Any]] = []

    for risk_id in sorted(risks):
        risk = risks[risk_id]
        track_counts[risk["track"]] += 1
        category_counts[risk["category"]] += 1
        remedy_type = risk["remedy_type"] or "none"
        remedy_type_counts[remedy_type] += 1

        function_id = risk["remedy_function"]
        if function_id:
            risk_to_function.append(
                {
                    "risk_id": risk_id,
                    "function_id": function_id,
                    "remedy_type": risk["remedy_type"],
                    "track": risk["track"],
                    "category": risk["category"],
                    "source_path": risk["source_path"],
                }
            )
            if function_id in function_to_risks:
                function_to_risks[function_id].append(risk_id)
            else:
                missing_function_defs.append(
                    {
                        "risk_id": risk_id,
                        "function_id": function_id,
                        "source_path": risk["source_path"],
                    }
                )

    for function_id in function_to_risks:
        function_to_risks[function_id] = sorted(set(function_to_risks[function_id]))

    function_declares_missing_risks: list[dict[str, Any]] = []
    function_ccve_link_mismatches: list[dict[str, Any]] = []
    for function_id in sorted(functions):
        function = functions[function_id]
        for risk_id in function["ccves"]:
            risk = risks.get(risk_id)
            if risk is None:
                function_declares_missing_risks.append(
                    {
                        "function_id": function_id,
                        "risk_id": risk_id,
                        "function_source": function["source_path"],
                    }
                )
                continue
            expected = risk["remedy_function"]
            if expected and expected != function_id:
                function_ccve_link_mismatches.append(
                    {
                        "risk_id": risk_id,
                        "expected_function_id": expected,
                        "declared_function_id": function_id,
                        "function_source": function["source_path"],
                    }
                )

    function_to_risks_list = [
        {
            "function_id": function_id,
            "risk_ids": function_to_risks[function_id],
            "source_path": functions[function_id]["source_path"],
        }
        for function_id in sorted(functions)
    ]

    unreferenced_functions = [
        {
            "function_id": function_id,
            "declared_risk_ids": functions[function_id]["ccves"],
            "source_path": functions[function_id]["source_path"],
        }
        for function_id in sorted(functions)
        if not function_to_risks[function_id]
    ]

    report = {
        "schema_version": "risk-function-links-v1",
        "summary": {
            "total_risks": len(risks),
            "total_functions": len(functions),
            "risks_with_function_ref": len(risk_to_function),
            "risks_without_function_ref": len(risks) - len(risk_to_function),
            "missing_function_definitions": len(missing_function_defs),
            "function_declares_missing_risks": len(function_declares_missing_risks),
            "function_ccve_link_mismatches": len(function_ccve_link_mismatches),
            "unreferenced_functions": len(unreferenced_functions),
            "track_counts": _as_sorted_counter(track_counts),
            "category_counts": _as_sorted_counter(category_counts),
            "remedy_type_counts": _as_sorted_counter(remedy_type_counts),
        },
        "links": {
            "risk_to_function": risk_to_function,
            "function_to_risks": function_to_risks_list,
            "missing_function_definitions": sorted(
                missing_function_defs, key=lambda item: (item["risk_id"], item["function_id"])
            ),
            "function_declares_missing_risks": sorted(
                function_declares_missing_risks,
                key=lambda item: (item["function_id"], item["risk_id"]),
            ),
            "function_ccve_link_mismatches": sorted(
                function_ccve_link_mismatches,
                key=lambda item: (item["risk_id"], item["declared_function_id"]),
            ),
            "unreferenced_functions": unreferenced_functions,
        },
    }

    output_bytes = _json_bytes(report)
    matches, changed = _write_or_check(output_path, output_bytes, args.check)

    print("Risk/function links summary")
    print(f"  total risks:                      {report['summary']['total_risks']}")
    print(f"  total functions:                  {report['summary']['total_functions']}")
    print(f"  risks with function ref:          {report['summary']['risks_with_function_ref']}")
    print(f"  missing function definitions:     {report['summary']['missing_function_definitions']}")
    print(f"  function declares missing risks:  {report['summary']['function_declares_missing_risks']}")
    print(f"  link mismatches:                  {report['summary']['function_ccve_link_mismatches']}")
    print(f"  unreferenced functions:           {report['summary']['unreferenced_functions']}")

    if args.check:
        if not matches:
            print(f"CHECK FAILED: {output_path} is out of date")
        return 1 if changed else 0

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

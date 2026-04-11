#!/usr/bin/env python3
"""Validate operator recipe schema and recipe files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema package required. Install with: pip install jsonschema")
    sys.exit(1)


SCHEMA_PATH = Path("schema/operator-recipe-v1.schema.json")
RECIPES_DIR = Path("recipes")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_schema(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        errors.append(f"Invalid JSON Schema: {exc.message}")
    return errors


def validate_doc(validator: Draft202012Validator, path: Path, doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for error in validator.iter_errors(doc):
        location = ".".join(str(part) for part in error.absolute_path)
        if location:
            errors.append(f"{path}: {location}: {error.message}")
        else:
            errors.append(f"{path}: {error.message}")
    return errors


def main() -> int:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema not found: {SCHEMA_PATH}")
        return 1

    schema = load_json(SCHEMA_PATH)
    schema_errors = validate_schema(schema)
    if schema_errors:
        for error in schema_errors:
            print(f"ERROR: {error}")
        return 1

    validator = Draft202012Validator(schema)
    recipe_files = sorted(path for path in RECIPES_DIR.rglob("*.yaml"))
    if not recipe_files:
        print(f"ERROR: no recipe files found under {RECIPES_DIR}")
        return 1

    errors: list[str] = []
    seen_ids: set[str] = set()

    for recipe_path in recipe_files:
        doc = load_yaml(recipe_path)
        if not isinstance(doc, dict):
            errors.append(f"{recipe_path}: top-level YAML document must be an object")
            continue

        errors.extend(validate_doc(validator, recipe_path, doc))

        recipe_id = str(doc.get("id", "")).strip()
        if recipe_id:
            if recipe_id in seen_ids:
                errors.append(f"{recipe_path}: duplicate recipe id {recipe_id!r}")
            seen_ids.add(recipe_id)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Operator recipe validation passed")
    print(f"  schema: {SCHEMA_PATH}")
    print(f"  recipes checked: {len(recipe_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate every results_v4 release in this repo against the canonical schemas.

The schemas live in the `common/` submodule (openproblems-bio/common_resources,
`schemas/results_v4/`). Each release directory `<task>/<version>/` holds the six
per-release JSON files; every present file is validated against its matching
sub-schema. `metric_info.json` is optional; the other five are required.

Usage:
    python scripts/validate_results.py [--schema-dir DIR] [--root DIR]
Exits non-zero if any file is missing, invalid JSON, or fails its schema.
"""
import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

# Per-release file -> schema file in schemas/results_v4. metric_info is optional.
PARTS = {
    "task_info.json": "task_info.json",
    "dataset_info.json": "dataset_info.json",
    "method_info.json": "method_info.json",
    "metric_info.json": "metric_info.json",
    "quality_control.json": "quality_control.json",
    "results.json": "results.json",
}
OPTIONAL = {"metric_info.json"}


def load_schemas(schema_dir: Path):
    if not schema_dir.is_dir():
        sys.exit(
            f"Schema dir not found: {schema_dir}\n"
            "Did you check out submodules? Run: git submodule update --init --recursive"
        )
    resources, by_file = [], {}
    for f in sorted(schema_dir.glob("*.json")):
        schema = json.loads(f.read_text())
        sid = schema.get("$id")
        if not sid:
            sys.exit(f"Schema {f} is missing a $id")
        resources.append((sid, Resource.from_contents(schema)))
        by_file[f.name] = schema
    if not by_file:
        sys.exit(f"No schema files found in {schema_dir}")
    # Refs between schemas resolve locally via the registry, so no network needed.
    return Registry().with_resources(resources), by_file


def main() -> int:
    here = Path(__file__).resolve().parent
    repo = here.parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=repo, help="results repo root")
    ap.add_argument(
        "--schema-dir",
        type=Path,
        default=repo / "common" / "schemas" / "results_v4",
        help="directory holding the results_v4 schema files",
    )
    args = ap.parse_args()

    registry, by_file = load_schemas(args.schema_dir)
    validators = {
        fname: Draft202012Validator(by_file[sfile], registry=registry)
        for fname, sfile in PARTS.items()
        if sfile in by_file
    }

    releases = sorted(p.parent for p in args.root.glob("*/*/task_info.json"))
    if not releases:
        sys.exit("No releases found (expected <task>/<version>/task_info.json).")

    errors = []
    for rel in releases:
        name = rel.relative_to(args.root)
        for fname in PARTS:
            fpath = rel / fname
            if not fpath.exists():
                if fname not in OPTIONAL:
                    errors.append(f"{name}/{fname}: MISSING")
                continue
            try:
                data = json.loads(fpath.read_text())
            except json.JSONDecodeError as e:
                errors.append(f"{name}/{fname}: invalid JSON: {e}")
                continue
            for err in sorted(validators[fname].iter_errors(data), key=lambda e: list(e.absolute_path)):
                loc = "/".join(str(p) for p in err.absolute_path) or "(root)"
                errors.append(f"{name}/{fname}: {loc}: {err.message}")
        print(f"checked {name}")

    if errors:
        print(f"\n{len(errors)} validation error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"\nAll {len(releases)} release(s) valid against results_v4 schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

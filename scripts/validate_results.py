#!/usr/bin/env python3
"""Validate every results_v4 release in this repo against the canonical schemas.

The results_v4 JSON Schemas are fetched from the common_resources repo at run
time. Each release directory `<task>/<version>/` holds the six per-release JSON
files; every present file is validated against its matching sub-schema.
`metric_info.json` is optional; the other five are required.

    python scripts/validate_results.py

Exits non-zero if any file is missing, invalid JSON, or fails its schema.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_BASE_URL = (
    "https://raw.githubusercontent.com/openproblems-bio/common_resources/main/schemas/results_v4"
)
# Schema files to load; core.json is referenced via $ref by the others.
SCHEMA_FILES = [
    "core.json",
    "task_info.json",
    "dataset_info.json",
    "method_info.json",
    "metric_info.json",
    "quality_control.json",
    "results.json",
    "task_results.json",
]

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


def fetch_json(url, attempts=3):
    last = None
    for i in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001
            last = e
            if i < attempts:
                time.sleep(0.5 * i)
    sys.exit(f"Could not fetch schema {url}: {last}")


def load_registry():
    """Fetch the schemas and index them by $id so $refs resolve locally (no per-ref network)."""
    by_file = {name: fetch_json(f"{SCHEMA_BASE_URL}/{name}") for name in SCHEMA_FILES}
    resources = []
    for name, schema in by_file.items():
        sid = schema.get("$id")
        if not sid:
            sys.exit(f"Schema {name} is missing a $id")
        resources.append((sid, Resource.from_contents(schema)))
    return Registry().with_resources(resources), by_file


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    registry, by_file = load_registry()
    validators = {
        fname: Draft202012Validator(by_file[sfile], registry=registry)
        for fname, sfile in PARTS.items()
    }

    releases = sorted(p.parent for p in root.glob("*/*/task_info.json"))
    if not releases:
        sys.exit("No releases found (expected <task>/<version>/task_info.json).")

    errors = []
    for rel in releases:
        name = rel.relative_to(root)
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

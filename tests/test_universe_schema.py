"""Schema validation tests: does the JSON conform?

Layer 1 of universe testing. Layer 2 (integrity) lives in
test_universe_integrity.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # afterburner/
SCHEMA_PATH = ROOT / "schemas" / "universe.schema.json"
FIXTURE_PATH = HERE / "fixtures" / "universe.json"


def load_schema() -> dict:
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)


def load_universe() -> dict:
    with open(FIXTURE_PATH, "r") as f:
        return json.load(f)


def test_universe_validates_against_schema() -> None:
    schema = load_schema()
    universe = load_universe()

    validator = Draft7Validator(schema)

    errors = list(validator.iter_errors(universe))

    assert not errors, "\n".join(
        f"{e.json_path}: {e.message}" for e in errors
    )

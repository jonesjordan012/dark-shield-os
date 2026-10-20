"""Entity tests: the M1 canonical model round-trips cleanly.

Checkpoint: for every entity type,
    entity -> to_node_dict() -> from_node_dict() -> equal entity,
and the serialized node validates against universe.schema.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from darkshield.entities import Entity, Galaxy, NeutronStar, Pulsar, Star

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE.parent / "schemas" / "universe.schema.json"


def _node_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    return schema["definitions"]["node"]


def _assert_roundtrip(entity: Entity) -> None:
    blob = entity.to_node_dict()
    clone = Entity.from_node_dict(blob)
    assert clone == entity
    assert clone.to_node_dict() == blob


def test_star_creation() -> None:
    star = Star(
        id="star:001",
        name="main.py",
        path="main.py",
        size_bytes=10,
        created_at=None,  # type: ignore[arg-type]
        updated_at=None,  # type: ignore[arg-type]
    )
    assert star.id == "star:001"


def test_star_roundtrip() -> None:
    star = Star(
        id="star:001",
        name="main.py",
        path="/proj/main.py",
        size_bytes=1024,
        sha256="abc123",
    )
    _assert_roundtrip(star)


def test_pulsar_roundtrip() -> None:
    pulsar = Pulsar(
        id="pulsar:001",
        name="python",
        pid=4248,
        cpu_percent=18.2,
        memory_mb=92.4,
    )
    _assert_roundtrip(pulsar)


def test_neutron_star_roundtrip() -> None:
    core = NeutronStar(
        id="core:0",
        name="CPU Core 0",
        core_index=0,
        utilization=36.0,
    )
    _assert_roundtrip(core)


def test_galaxy_roundtrip() -> None:
    galaxy = Galaxy(
        id="galaxy:dev",
        name="Development",
        kind="directory",
        continuity=0.81,
    )
    _assert_roundtrip(galaxy)


def test_galaxy_rejects_m3_kind() -> None:
    with pytest.raises(ValueError):
        Galaxy(id="galaxy:bad", name="Bad", kind="development")


def test_canonical_derived_exclusive() -> None:
    with pytest.raises(ValueError):
        Star(id="s", name="s", canonical=True, derived=True)


def test_serialized_nodes_validate_against_schema() -> None:
    node_schema = _node_schema()
    validator = Draft7Validator(node_schema)
    entities: list[Entity] = [
        Star(id="star:001", name="a.py", path="a.py", size_bytes=10),
        Pulsar(id="pulsar:001", name="python", pid=1),
        NeutronStar(id="core:0", name="Core 0", core_index=0),
        Galaxy(id="galaxy:d", name="D", kind="directory"),
    ]
    for entity in entities:
        errors = list(validator.iter_errors(entity.to_node_dict()))
        assert not errors, [e.message for e in errors]


def test_from_node_dict_rejects_unknown_type() -> None:
    with pytest.raises(ValueError):
        Entity.from_node_dict(
            {"id": "x:1", "type": "black_hole", "name": "X"}
        )

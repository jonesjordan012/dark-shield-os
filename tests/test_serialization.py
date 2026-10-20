"""Serialization tests: the M1 round-trip layer.

Every entity round-trips: entity -> dict -> entity, and
entity -> json -> entity. The Universe round-trips through
universe.json: save -> load -> equal universe.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from darkshield import (
    Evidence,
    Galaxy,
    NeutronStar,
    Pulsar,
    Relationship,
    Star,
    Universe,
)


def test_star_dict_roundtrip() -> None:
    star = Star(
        id="star:001",
        name="demo.py",
        path="demo.py",
        size_bytes=42,
        sha256=None,
        created_at=None,  # type: ignore[arg-type]
        updated_at=None,  # type: ignore[arg-type]
    )
    blob = star.to_dict()
    star2 = Star.from_dict(blob)
    assert star == star2


def test_pulsar_dict_roundtrip() -> None:
    pulsar = Pulsar(
        id="pulsar:001", name="python", pid=4248,
        cpu_percent=18.2, memory_mb=92.4,
    )
    assert Pulsar.from_dict(pulsar.to_dict()) == pulsar


def test_neutron_star_dict_roundtrip() -> None:
    core = NeutronStar(
        id="core:0", name="CPU Core 0", core_index=0, utilization=36.0
    )
    assert NeutronStar.from_dict(core.to_dict()) == core


def test_galaxy_dict_roundtrip() -> None:
    galaxy = Galaxy(
        id="galaxy:dev", name="Development",
        kind="directory", continuity=0.81,
    )
    assert Galaxy.from_dict(galaxy.to_dict()) == galaxy


def test_entity_json_roundtrip() -> None:
    star = Star(id="star:001", name="demo.py", path="demo.py", size_bytes=42)
    blob = json.dumps(star.to_dict())
    star2 = Star.from_dict(json.loads(blob))
    assert star == star2


def test_relationship_dict_roundtrip() -> None:
    rel = Relationship(
        id="rel:1", source="galaxy:dev", target="star:001",
        relation="contains", weight=1.0,
    )
    rel.attach_evidence(
        Evidence(
            source="dependency", observations=14, confidence=0.82,
            details={"reason": "imported_together"},
        )
    )
    assert Relationship.from_dict(rel.to_dict()) == rel


def test_relationship_rejects_unknown_relation() -> None:
    with pytest.raises(ValueError):
        Relationship(
            id="rel:x", source="a", target="b", relation="teleports_to"
        )


def test_relationship_rejects_bad_weight() -> None:
    with pytest.raises(ValueError):
        Relationship(
            id="rel:x", source="a", target="b",
            relation="contains", weight=1.5,
        )


def _build_universe() -> Universe:
    universe = Universe(universe_id="urn:darkshield:universe:test")
    star = Star(id="star:001", name="demo.py", path="demo.py", size_bytes=42)
    galaxy = Galaxy(id="galaxy:dev", name="Development", kind="directory")
    universe.add(star)
    universe.add(galaxy)
    universe.add_relationship(
        Relationship(
            id="rel:1", source="galaxy:dev", target="star:001",
            relation="contains", weight=1.0,
        )
    )
    universe.record("galaxy:dev", "continuity_updated",
                    {"old_score": 0.72, "new_score": 0.81})
    return universe


def test_universe_save_load_roundtrip() -> None:
    universe = _build_universe()
    with tempfile.TemporaryDirectory() as tmp:
        path = universe.save(Path(tmp) / "universe.json")
        universe2 = Universe.load(path)
    assert universe2 == universe


def test_universe_rejects_duplicate_node_id() -> None:
    universe = Universe(universe_id="test")
    universe.add(Star(id="star:001", name="a.py", path="a.py", size_bytes=1))
    with pytest.raises(ValueError):
        universe.add(Star(id="star:001", name="b.py", path="b.py", size_bytes=2))


def test_universe_rejects_dangling_relationship() -> None:
    universe = Universe(universe_id="test")
    universe.add(Star(id="star:001", name="a.py", path="a.py", size_bytes=1))
    with pytest.raises(ValueError):
        universe.add_relationship(
            Relationship(id="rel:1", source="star:001",
                         target="star:999", relation="depends_on")
        )


def test_saved_universe_validates_against_schema() -> None:
    import json as _json

    from jsonschema import Draft7Validator

    schema_path = (
        Path(__file__).resolve().parent.parent
        / "schemas" / "universe.schema.json"
    )
    with open(schema_path) as f:
        schema = _json.load(f)

    universe = _build_universe()
    with tempfile.TemporaryDirectory() as tmp:
        path = universe.save(Path(tmp) / "universe.json")
        with open(path) as f:
            doc = _json.load(f)

    errors = list(Draft7Validator(schema).iter_errors(doc))
    assert not errors, [e.message for e in errors]
